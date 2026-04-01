from marshmallow import Schema, fields, validate


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True, 
        validate=[
            validate.Length(min=8),
            validate.Regexp(r'.*[A-Z].*', error='Must contain at least 1 uppercase letter'),
            validate.Regexp(r'.*[0-9].*', error='Must contain at least 1 number'),
            validate.Regexp(r'.*[^A-Za-z0-9].*', error='Must contain at least 1 special character')
        ]
    )
    name = fields.Str(
        required=True, 
        validate=[
            validate.Length(min=3, error='Name must be at least 3 characters'),
            validate.Regexp(r'.*[a-zA-Z].*', error='Name must contain at least one letter')
        ]
    )


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


class UserSchema(Schema):
    id = fields.Integer(dump_only=True)
    email = fields.Email(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class PasswordResetRequestSchema(Schema):
    email = fields.Email(required=True)

class PasswordResetConfirmSchema(Schema):
    email = fields.Email(required=True)
    code = fields.String(required=True, validate=validate.Length(equal=6))
    new_password = fields.String(
        required=True, 
        validate=[
            validate.Length(min=8),
            validate.Regexp(r'.*[A-Z].*', error='Must contain at least 1 uppercase letter'),
            validate.Regexp(r'.*[0-9].*', error='Must contain at least 1 number'),
            validate.Regexp(r'.*[^A-Za-z0-9].*', error='Must contain at least 1 special character')
        ]
    )
