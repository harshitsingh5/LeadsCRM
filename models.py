from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db=SQLAlchemy()

# user -> lead      one-many
# lead -> Remark  one-many

class User_details(db.Model):
    __tablename__="user_details"
    user_id=db.Column(db.Integer,primary_key=True)
    account_type=db.Column(db.Integer,default=0)   #0-channel partner, 1-sales person, 2-manager, 3-site-engineer, 4-account-officer, 5-store manager
    channel_partner_type=db.Column(db.Integer,default=100)   #0-designer, 1-architect, 2-individual, 3-channel partner, 100-nothing
    name=db.Column(db.String(50))
    mobile_no=db.Column(db.String(13))
    email=db.Column(db.String(50))
    password=db.Column(db.String(200))
    verified=db.Column(db.Boolean,default=False)
    profile_picture=db.Column(db.String(200))
    cp_total_earning=db.Column(db.Integer,default=0)
    c_token=db.Column(db.String(10))
    updated=db.Column(db.Boolean,default=False)      #verified=1  unverified=0
    company_id=db.Column(db.Integer,db.ForeignKey("company_details.company_id"))
    lead=db.relationship("Leads", cascade="all,delete",backref=db.backref("user"))   #ONLY FOR CHANNEL PARTNER
    notif=db.relationship("Notifications", cascade="all,delete",backref=db.backref("user"))

class Client_details(db.Model):
    __tablename__="client_details"
    client_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))
    mobile_number=db.Column(db.String(10))
    email=db.Column(db.String(50))
    address1=db.Column(db.String(40))
    address2=db.Column(db.String(40))
    # locality=db.Column(db.String(40))
    # street=db.Column(db.String(40))
    # area=db.Column(db.String(40))
    city=db.Column(db.String(30))
    state=db.Column(db.String(20))
    pincode=db.Column(db.String(6))

class Company_details(db.Model):
    __tablename__="company_details"
    company_id=db.Column(db.Integer,primary_key=True)
    company_name=db.Column(db.String(50))
    contact_person_name=db.Column(db.String(50))
    contact_person_contact_no=db.Column(db.String(13))
    alternate_number=db.Column(db.String(13))
    gst_no=db.Column(db.String(15))
    pan_no=db.Column(db.String(10))
    upi_no=db.Column(db.String(25))
    visiting_card=db.Column(db.LargeBinary)
    account_number=db.Column(db.String(25))
    ifsc=db.Column(db.String(15))
    name=db.Column(db.String(40))
    bank=db.Column(db.String(40))
    branch=db.Column(db.String(30))

class Otp_details(db.Model):
    __tablename__="otp_details"
    otp_id=db.Column(db.Integer,primary_key=True)
    otp_for=db.Column(db.Integer)           #0-channel partner, 1-sales person, 2-manager, 3-site-engineer, 4-account-officer
    user_id=db.Column(db.Integer,db.ForeignKey("user_details.user_id"), nullable=True)
    otp_no=db.Column(db.Integer,nullable=False)
    purpose=db.Column(db.Boolean)           #password change=0   verification=1
    valid_till=db.Column(db.DateTime)     #store time and date upto which otp is valid_till

class Leads(db.Model):
    __tablename__="leads"
    lead_id=db.Column(db.Integer,primary_key=True)
    channel_partner_id=db.Column(db.Integer,db.ForeignKey("user_details.user_id"))
    generation_date=db.Column(db.DateTime,default=datetime.now())
    sales_id=db.Column(db.Integer)
    manager_id=db.Column(db.Integer)
    site_engineer_id=db.Column(db.Integer)
    account_officer_id=db.Column(db.Integer)
    client_id=db.Column(db.Integer,db.ForeignKey("client_details.client_id"))
    enquiry_for=db.Column(db.String(50))
    package_type=db.Column(db.String(50))
    enquiry_type=db.Column(db.String(50))
    poc_type=db.Column(db.String(50))
    poc_ppf=db.Column(db.String(50))
    welcome_call=db.Column(db.Boolean, default=False)
    welcome_email=db.Column(db.Boolean, default=False)
    initial_offer=db.Column(db.String(200))
    renegotiate=db.Column(db.String(2000))
    installments=db.Column(db.String(50))
    follow_up_status_dios=db.Column(db.String(50))
    last_updated_on=db.Column(db.DateTime)
    lead_status_for_cp=db.Column(db.Integer,default=0)     #cp 0-Pending, 1-Active, 2-Completed, 3-Rejected
    lead_status_by_manager=db.Column(db.Integer, default=0)      #mngr 0-Unattended (by sales), 1-Active, 2-Completed, 22-Completed By Manager(Pay Channel Partner), 3-Closed, 33-closed by manager 4-Dismissed, 5-Dismissed_by_Sales
    lead_status_by_sales=db.Column(db.Integer, default=0)      #sales 0-Pending, 1-Active, 11-Active_done 2-Negotiate, 22-Negotiate_done 3-Product_Ready 4-Completed, 5-Dismissed
    lead_status_by_site_engineer=db.Column(db.Integer, default=0)      #site 0-Pending, 1-Visit in Progress, 2-Visited, 3-To be Installed 4-Completed
    lead_status_by_account_officer=db.Column(db.Integer, default=0)     #acc 1-Check Initial Payment,11-done, 2-Check Full Payment, 22-done, 3-Pay Channel Partner, 4-Completed
    lead_status=db.Column(db.Integer,default=0)   #0-6    #0-Pending, 1-Active, 2-closed, 3-dismissed
    lead_status_remark=db.Column(db.String(5000))
    no_of_client_meetings=db.Column(db.Integer)
    site_measurements=db.Column(db.String(50))
    revision_number=db.Column(db.Integer)
    order_value=db.Column(db.Float)
    install_date_remark=db.Column(db.String(200))
    invoice_uploaded=db.Column(db.Boolean, default=False)
    invoice_filename=db.Column(db.String(50))
    confirmation_filename=db.Column(db.String(50))
    c_token=db.Column(db.String(10))
    remarks=db.relationship("Remarks", cascade="all,delete",backref=db.backref("of_lead"))    # lead -> Remarks  one-many

class Remarks(db.Model):
    __tablename__="remarks"
    remark_id=db.Column(db.Integer,primary_key=True)
    lead_id=db.Column(db.Integer,db.ForeignKey("leads.lead_id"))    # lead -> Sequence  one-many
    user_id=db.Column(db.Integer,db.ForeignKey("user_details.user_id"))
    account_type=db.Column(db.Integer,default=0)   #0-channel partner, 1-sales person, 2-designer, 3-manager, 4-site engineer, 5-account manager
    date=db.Column(db.DateTime,default=datetime.now())
    remark=db.Column(db.String(400))

# class Sequence(db.Model):                           #store the process and accessibility of content
#     seq_id=db.Column(db.Integer,primary_key=True)
#     lead_id=db.Column(db.Integer,db.ForeignKey("leads.lead_id"))    # lead -> Sequence  one-many
#     current_count=db.Column(db.Integer)
#     total_counts=db.Column(db.Integer)
#     user_type=db.Column(db.Integer)
#     user_id=db.Column(db.Integer,db.ForeignKey("user_details.user_id"))

class Notifications(db.Model):
    __tablename__="notifications"
    not_id=db.Column(db.Integer,primary_key=True)
    subject=db.Column(db.String(50))
    user_id=db.Column(db.Integer,db.ForeignKey("user_details.user_id"))
    message=db.Column(db.String(200))

class Images(db.Model):
    image_id=db.Column(db.Integer,primary_key=True)
    user_type=db.Column(db.Integer)
    user_id=db.Column(db.Integer,db.ForeignKey("user_details.user_id"))
    image_file=db.Column(db.LargeBinary)


# RELATIONS START HERE--------------------------------------------------
# class Rel_user_lead(db.Model):                   # user -> lead      many-many
#     __tablename__="rel_user_lead"
#     ul_id=db.Column(db.Integer,primary_key=True)
#     user_id=db.Column(db.Integer,db.ForeignKey("user_details.user_id"))
#     lead_id=db.Column(db.Integer,db.ForeignKey("leads.lead_id"))
