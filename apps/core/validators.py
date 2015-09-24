import re
from wtforms import validators


name_pattern = re.compile(r'^[a-zа-я]*$', re.IGNORECASE)
name_validator = validators.Regexp(name_pattern, message='Name is incorrect.')

phone_pattern = re.compile(r'''
            # don't match beginning of string, number can start anywhere
(\d{3})     # area code is 3 digits (e.g. '800')
\D*         # optional separator is any number of non-digits
(\d{3})     # trunk is 3 digits (e.g. '555')
\D*         # optional separator
(\d{4})     # rest of number is 4 digits (e.g. '1212')
\D*         # optional separator
(\d*)       # extension is optional and can be any number of digits
$           # end of string
''', re.VERBOSE)
phone_validator = validators.Regexp(phone_pattern,
                                    message='Phone is incorrect.')
