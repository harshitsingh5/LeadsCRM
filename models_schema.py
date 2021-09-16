from flask_marshmallow import Marshmallow
import models

class User_details_S(ma.ModelSchema):
    class Meta:
        model = User_details

class Client_details_S(ma.ModelSchema):
    class Meta:
        model = Client_details

class Company_details_S(ma.ModelSchema):
    class Meta:
        model = Company_details

class Otp_details_S(ma.ModelSchema):
    class Meta:
        model = Otp_details

class Leads_S(ma.ModelSchema):
    class Meta:
        model = Leads

class Sequence_S(ma.ModelSchema):
    class Meta:
        model = Sequence

class Notifications_S(ma.ModelSchema):
    class Meta:
        model = Notifications

class Images_S(ma.ModelSchema):
    class Meta:
        model = Images

class Rel_user_lead_S(ma.ModelSchema):
    class Meta:
        model = Rel_user_lead
