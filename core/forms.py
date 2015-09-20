import logging

from wtforms_tornado import Form as WTForm
from schematics.exceptions import ValidationError as ModelValidationError
from wtforms import StringField, PasswordField, validators
from wtforms.validators import ValidationError

from .models import User

logger = logging.getLogger(__name__)


class EmptyException(Exception):
    pass


class Form(WTForm):
    def get_err_msg(self, err_code):
        text_errors = getattr(self, 'text_errors', {})
        return text_errors.get(err_code, err_code)

    def set_field_error(self, field_name, err_code):
        """
        Adds given error message to given field_name.
        First, it tries to find error message in self.text_errors dict by
        `err_code` key. If not find, just set error message to err_code.
        """
        err_msg = self.get_err_msg(err_code)
        getattr(self, field_name).errors.append(err_msg)

    def set_nonfield_error(self, err_code):
        err_msg = self.get_err_msg(err_code)
        if self._errors is None:
            self._errors = {}
        self._errors.set_default('whole_form', [])
        self.errors['whole_form'].append(err_msg)
        getattr(self, 'field_name').errors.append(err_msg)


class ModelForm(Form):
    """
    Form, that is linked to model.
    Example:
    class MyMorm(ModelForm):
        email = StringField('Email Address', [validators.InputRequired()])
        _model = MyModel # required
    _model must contain model class
    In addition to Form validation, performs validation from model.
    If validation passes, model object can be accessed by `get_object` method.
    """
    # TODO
    # create form fields from provided model dynamically.
    # Not to duplicate the code, i.e. repeating fields in model and in from.

    # TODO
    # find a way to perform validation, that depends on database access
    # currently, if function is wrapped with @gen.coroutine, exception
    # is ignored

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self._model_object = None

    def get_object(self):
        return self._model_object

    def get_model(self):
        model = getattr(self, '_model', None)
        if model is None:
            raise EmptyException()
        return model

    def validate(self):
        valid = super(ModelForm, self).validate()
        model = self.get_model()
        obj = model()
        self.populate_obj(obj)
        try:
            obj.validate()
        except ModelValidationError as e:
            if isinstance(e.messages, dict):
                for field_name, err_msgs in e.messages.items():
                    errors = getattr(self, field_name).errors
                    if not errors:
                        errors.extend(err_msgs)
            else:
                logger.warning("Unknown validation error: '{0}'".format(e))
                self.set_nonfield_error("Unknown error.")
            return False
        self._model_object = obj
        return valid


class RegistrationForm(ModelForm):
    name = StringField('Name')
    email = StringField('Email Address', [validators.InputRequired(),
                                          validators.Email()])
    password = PasswordField('Password', [validators.InputRequired()])
    password_confirmation = PasswordField('Repeat password',
                                          [validators.InputRequired()])

    _model = User
    text_errors = {
        "password_mismatch": "Password mismatch",
        "email_occupied": "Already taken",
    }

    def validate_password_confirmation(self, field):
        if self.password.data != field.data:
            raise ValidationError(self.text_errors['password_mismatch'])


class LoginForm(Form):
    email = StringField('Email Address', [validators.InputRequired(),
                                          validators.Email()])
    password = PasswordField('Password', [validators.InputRequired()])

    text_errors = {
        'not_found': "Email and password mismatch",
        'wrong_password': "Email and password mismatch",
    }


class AccountForm(Form):
    pass


class EventForm(Form):
    pass
