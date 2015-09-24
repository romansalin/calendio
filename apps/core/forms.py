import logging

from wtforms_tornado import Form as WTForm
from schematics.exceptions import ValidationError as ModelValidationError

logger = logging.getLogger(__name__)


class EmptyException(Exception):
    pass


class Form(WTForm):
    def set_field_error(self, field_name, err_code):
        err_msg = self._get_err_msg(err_code)
        getattr(self, field_name).errors.append(err_msg)

    def set_nonfield_error(self, err_code):
        err_msg = self._get_err_msg(err_code)
        if self._errors is None:
            self._errors = {}
        self._errors.setdefault('whole_form', [])
        self.errors['whole_form'].append(err_msg)

    def _get_err_msg(self, err_code):
        text_errors = getattr(self, 'text_errors', {})
        return text_errors.get(err_code, err_code)


class ModelForm(Form):
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
                logger.warning('Unknown validation error: "{0}".'.format(e))
                self.set_nonfield_error('Unknown error.')
            return False
        self._model_object = obj
        return valid
