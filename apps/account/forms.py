from wtforms import (StringField, PasswordField, DateField, SelectField,
                     validators)
from wtforms.validators import ValidationError

from ..core.forms import Form, ModelForm
from ..core.validators import name_validator, phone_validator
from .models import User


class EmptyException(Exception):
    pass


class RegistrationForm(ModelForm):
    name = StringField('Name', [name_validator])
    email = StringField('Email', [validators.InputRequired(),
                                  validators.Email()])
    password = PasswordField('Password', [validators.InputRequired()])
    password_confirmation = PasswordField('Repeat password',
                                          [validators.InputRequired()])

    _model = User
    text_errors = {
        'password_mismatch': 'Password mismatch.',
        'email_occupied': 'Already taken.',
    }

    def validate_password_confirmation(self, field):
        if self.password.data != field.data:
            raise ValidationError(self.text_errors['password_mismatch'])


class LoginForm(Form):
    email = StringField('Email', [validators.InputRequired(),
                                  validators.Email()])
    password = PasswordField('Password', [validators.InputRequired()])

    text_errors = {
        'email_or_password_error': 'The username or password you entered is '
                                   'incorrect.',
    }


class ProfileForm(ModelForm):
    name = StringField('Name', [name_validator])
    email = StringField('Email', [validators.InputRequired(),
                                  validators.Email()])
    phone = StringField('Phone', [phone_validator])
    # city_id = SelectField('City')
    photo = StringField('Photo')
    birth_date = DateField('Date of Birth', [])

    _model = User
    text_errors = {

    }
