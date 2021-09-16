from flask import Flask,render_template,redirect,url_for,request,jsonify,send_file,session
from models import *
import uuid
import random
import string
from datetime import datetime,timedelta
from flask_marshmallow import Marshmallow
from passlib.hash import sha256_crypt
import json
import requests
from flask_migrate import Migrate
import base64
import io


app=Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@localhost/leads"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
db.app=app

migrate = Migrate(app, db)


ma=Marshmallow(app)


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



def pass_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def get_tokken():
	tokken=""
	while True:
		tokken=pass_generator()
		x=User_details.query.filter_by(c_token=tokken).all()
		if len(x)==0:
			break
	return tokken

#APIs FOR APP

@app.route("/login-app",methods=["GET","POST"])
def inflogin():
	# try:
	if request.method=="POST":
		data = request.json
		user=User_details.query.filter_by(mobile_no=data['mobile_no']).all()
		if len(user)==0:
			user=User_details(mobile_no=data["mobile_no"],c_token=get_tokken(),account_type=0)
			db.session.add(user)
			db.session.commit()
			otp=random.randint(1000,9999)
			otp_obj=Otp_details(otp_for=0,user_id=user.user_id,otp_no=otp,purpose=1,valid_till=datetime.now()+timedelta(hours=1))
			db.session.add(otp_obj)
			db.session.commit()
			# send_sms(str(otp),data["mobile_no"])
			return jsonify(valid=True,tokken=user.c_token,updated=False)
		else:
			otp_no=Otp_details.query.filter_by(user_id=user[0].user_id).all()
			for ot in otp_no:
				db.session.delete(ot)
			db.session.commit()
			c_tokken=get_tokken()
			user[0].c_token=c_tokken
			otp=random.randint(1000,9999)
			otp_obj=Otp_details(otp_for=0,user_id=user[0].user_id,otp_no=otp,purpose=1,valid_till=datetime.now()+timedelta(hours=1))
			db.session.add(otp_obj)
			db.session.commit()
			# send_sms(str(otp),data["mobile_no"])
			return jsonify(valid=True,tokken=user[0].c_token,updated=True,account_type=user[0].account_type)
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")
	# except:
	# 	return jsonify(valid=False,err="Some Thing Went Wrong!!!")

@app.route("/verify-otp-app",methods=["GET","POST"])
def verfiy_otp_inf():
	# try:
	if request.method=="POST":
		data = request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		updated=this_user.updated
		otp_no=Otp_details.query.filter_by(user_id=this_user.user_id).all()[-1]
		if otp_no.otp_no==int(data["otp"]):
				this_user.verified=True
				db.session.delete(otp_no)
				db.session.commit()
				return jsonify(valid=True,verified=True,updated=updated,account_type=int(this_user.account_type))
		else:
			return jsonify(valid=False,err="Wrong OTP or OTP Expired")
	else:
			return jsonify(valid=False,err="Method Not Allowed!!!")
	# except:
	# 	return jsonify(valid=False,err=data["tokken"])

@app.route("/submitdetails-app",methods=["GET","POST"])
def submitdetails_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		this_user.name=data["full_name"]
		this_user.email=data["email"]
		this_user.updated=True
		db.session.commit()
		return jsonify(valid=True)

@app.route("/channel-dash-app",methods=["GET","POST"])
def channel_dash_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		leads=this_user.lead
		lead_sch=Leads_S()
		active,pending,completed,rejected=0,0,0,0
		for lead in leads:
			if lead.status_for_cp==0:
				active+=1
			elif lead.status_for_cp==1:
				pending+=1
			elif lead.status_for_cp==2:
				completed+=1
			elif lead.status_for_cp==3:
				rejected+=1
		return jsonify(valid=True,data={"active":active,"pending":pending,"completed":completed,"rejected":rejected,"cp_total_earning":this_user.cp_total_earning})
@app.route("/channel-profile-app",methods=["GET","POST"])
def channel_profile_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		return jsonify(valid=True,data={"name":this_user.name,"mobile_no":this_user.mobile_no,"email":this_user.email,"account_type":this_user.account_type})


@app.route("/channel-notification-app",methods=["GET","POST"])
def channel_notification_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		notif_sch=Notifications_S()
		result=[]
		for n in this_user.notif:
			result.append(notif_sch.dump(n).data)
		return jsonify(valid=True,data=result)


@app.route("/createlead-app",methods=["GET","POST"])
def createlead_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		client=Client_details(name=data["name"],mobile_number=data["contact"])
		db.session.add(client)
		db.session.commit()
		lead=Leads(client_id=client.client_id)
		db.session.add(lead)
		db.session.commit()
		this_user.lead.append(lead)
		db.session.commit()
		return jsonify(valid=True,client_id=client.client_id,lead_id=lead.lead_id)


@app.route("/channel-activeleads-app",methods=["GET","POST"])
def channel_activeleads_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		leads=this_user.lead
		result=[]
		for lead in leads:
			if lead.status_for_cp==0:
				client=Client_details.query.filter_by(client_id=lead.client_id).first()
				result.append({"lead_id":lead.lead_id,"name":client.name,"state":client.state,"city":client.city})
		return jsonify(valid=True,data=result)


@app.route("/channel-pendingleads-app",methods=["GET","POST"])
def channel_pendingleads_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		leads=this_user.lead
		result=[]
		for lead in leads:
			if lead.status_for_cp==1:
				client=Client_details.query.filter_by(client_id=lead.client_id).first()
				result.append({"lead_id":lead.lead_id,"name":client.name,"state":client.state,"city":client.city})
		return jsonify(valid=True,data=result)
	

@app.route("/channel-rejectedleads-app",methods=["GET","POST"])
def channel_rejectedleads_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		leads=this_user.lead
		result=[]
		for lead in leads:
			if lead.status_for_cp==3:
				client=Client_details.query.filter_by(client_id=lead.client_id).first()
				result.append({"lead_id":lead.lead_id,"name":client.name,"state":client.state,"city":client.city})
		return jsonify(valid=True,data=result)
	


@app.route("/channel-completedleads-app",methods=["GET","POST"])
def channel_completedleads_app():
	if request.method=="POST":
		data=request.json
		c_tokken=data["tokken"]
		this_user=User_details.query.filter_by(c_token=c_tokken).first()
		leads=this_user.lead
		result=[]
		for lead in leads:
			if lead.status_for_cp==2:
				client=Client_details.query.filter_by(client_id=lead.client_id).first()
				result.append({"lead_id":lead.lead_id,"name":client.name,"state":client.state,"city":client.city})
		return jsonify(valid=True,data=result)
	


@app.route("/dashboard-channel-app",methods=["GET","POST"])
def dashboard_channel():
	#try:
	earning=cp_total_earning
	leads=user.lead
	a=0
	b=0
	c=0
	d=0
	for l in leads:
		if l.status_for_cp==0:
			a+=1
		if l.status_for_cp==1:
			b+=1
		if l.status_for_cp==1:
			c+=1
		if l.status_for_cp==1:
			d+=1
	return jsonify(valid=True,earning=earning,active=a,pending=b,completed=c,rejected=d)

@app.route("/create-lead2-app",methods=["GET","POST"])
def create_lead():
	# try:
	if request.method=="POST":
		#user=GetUserInfo()
		data=request.json
		c_token=data["tokken"]
		user=User_details.query.filter_by(c_token=c_token).first()
		# email=data['email']
		address1=data['address1']
		address2=data['address2']
		city=data['city']
		state=data['state']
		pincode=data['pincode']
		enquiry_for=data['enquiry_for']
		package_type=data['package_type']
		client=Client_details.query.filter_by(client_id=data["client_id"]).first()
		if not client:
			return jsonify(valid=False,err="No Client Found")
		lead=Leads.query.filter_by(lead_id=data["lead_id"]).first()
		if not lead:
			return jsonify(valid=False,err="No Lead Found")
		client.address1=address1
		client.address2=address2
		client.city=city
		client.state=state
		client.pincode=pincode
		lead.enquiry_for=enquiry_for
		lead.package_type=package_type
		db.session.commit()
		return jsonify(valid=True)
		# client=Client_details(name=name,mobile_no=mobile_no,email=email,address1=address1,address2=address2,city=city,state=state,pincode=pincode)
		# db.session.add(client)
		# db.session.commit()
		# ld=Leads(client_id=client.client_id,generation_date=datetime.now(),enquiry_for=enquiry_for,enquiry_type=enquiry_type)
		# db.session.add(ld)
		# user.lead.append(ld)
		# db.session.commit()
	# 	return jsonify(valid=True,message="Lead Created Successfully")
	# else:
	# 	#flash("Something Went Wrong")
	# 	return jsonify(valid=False)
	# except:
	# 	return jsonify(valid=False,err=str(data))

@app.route("/profile-app",methods=["GET","POST"])
def profile():
	# try:
	#user=GetUserInfo()
	data=request.json
	c_token=data["token"]
	user=User_details.query.filter_by(c_token=c_token).first()
	return jsonify(valid=True,account_type=user.account_type,channel_partner_type=user.channel_partner_type,name=user.name,mobile_no=user.mobile_no,email=user.email,verified=user.verified,profile_picture=user.profile_picture,cp_total_earning=user.cp_total_earning,updated=user.updated)

@app.route("/claim-incentives-app",methods=["GET","POST"])
def claim_incentives():
	# try:
	if request.method=="POST":
		data=request.json
		c_token=data["token"]
		user=User_details.query.filter_by(c_token=c_token).first()
		company_name=data["company_name"]
		contact_person_name=data["contact_person_name"]
		contact_person_contact_no=data["contact_person_contact_no"]
		alternate_number=data["alternate_number"]
		gst_no=data["gst_no"]
		pan_no=data["pan_no"]
		account_number=data["account_number"]
		ifsc=data["ifsc"]
		name=data["name"]
		bank=data["bank"]
		branch=data["branch"]
		c=Company_details(company_name=company_name,contact_person_name=contact_person_name,contact_person_contact_no=contact_person_contact_no,alternate_number=alternate_number,gst_no=gst_no,pan_no=pan_no,account_number=account_number,ifsc=ifsc,name=name,bank=bank,branch=branch)
		db.session.add(c)
		user.company_id.append(c)
		db.session.commit()
		return jsonify(valid=True,message="Applied for Claiming Incentives Successfully")
	else:
		return jsonify(valid=False)
	# except:
	# 	return jsonify(valid=False,err=str(data))

@app.route("/dashboard-channel/client-details-app",methods=["GET","POST"])
def client_details():
	#try:
	if request.method=="POST":
		data=request.json
		c_token=data["token"]
		lead=Leads.query.filter_by(c_token=c_token).first()
		client=lead.client_id
		cd=Client_details_S()
		result=cd.dump(client).data
		return jsonify(valid=True,result=result)
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")
	# except:
	# 	return jsonify(valid=False,err=str(data))








@app.route("/dashboard-sales-app",methods=["GET","POST"])
def dashboard_sales():
	#try:
	data=request.json
	c_token=data["token"]
	user=User_details.query.filter_by(c_token=c_token).first()
	leads=user.lead
	a=0
	d=0
	all_a=0
	for l in leads:
		if l.status_for_sales==0:
			a+=1
		if l.status_for_sales==1:
			d+=1
	all_approved=Leads.query.all()
	for a in all_approved:
		if a.lead_status==1:
			all_a+=1
	return jsonify(valid=True,active=a,done=d,all=all_a)

@app.route("/dashboard-sales/welcome-call-app",methods=["GET","POST"])
def welcome_call():
	#try:
	if request.method=="POST":
		data=request.json
		c_token=data["token"]
		lead=Leads.query.filter_by(c_token=c_token).first()
		lead.welcome_call=True
		db.session.commit()
		return jsonify(valid=True)
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")

@app.route("/dashboard-sales/welcome-call-remark-app",methods=["GET","POST"])
def welcome_call_remark():
	#try:
	if request.method=="POST":
		data=request.json
		r=data['remark']
		c_token=data["token"]
		lead=Leads.query.filter_by(c_token=c_token).first()
		rr=str(lead.remarks_sales)
		rr=rr+","+str(r)
		lead.remarks_sales=rr
		db.session.commit()
		#flash("Remark Added")
		return jsonify(valid=True, message="Remark Added")
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")

@app.route("/dashboard-sales/welcome-email-app",methods=["GET","POST"])
def welcome_email():
	#try:
	if request.method=="POST":
		data=request.json
		c_token=data["token"]
		lead=Leads.query.filter_by(c_token=c_token).first()
		lead.welcome_email=True
		db.session.commit()
		return jsonify(valid=True)
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")

@app.route("/dashboard-sales/welcome-email-remark-app",methods=["GET","POST"])
def welcome_email_remark():
	#try:
	if request.method=="POST":
		data=request.json
		r=data['remark']
		c_token=data["token"]
		lead=Leads.query.filter_by(c_token=c_token).first()
		rr=str(lead.remarks_sales)
		rr=rr+","+str(r)
		lead.remarks_sales=rr
		db.session.commit()
		#flash("Remark Added")
		return jsonify(valid=True, message="Remark Added")
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")

#-------------------check from here---------------
@app.route("/dashboard-sales/initial_offer-app",methods=["GET","POST"])
def initial_offer():
	#try:
	if request.method=="POST":
		data=request.json
		c_token=data["token"]
		lead=Leads.query.filter_by(c_token=c_token).first()
		# lead.initial_offer=True
		# db.session.commit()
		return jsonify(valid=True)
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")

@app.route("/dashboard-sales/initial_offer-remark-app",methods=["GET","POST"])
def initial_offer_remark():
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		data=request.json
		r=data['remark']
		c_token=data["token"]
		lead=Leads.query.filter_by(c_token=c_token).first()
		lead.initial_offer=r
		db.session.commit()
		#flash("Remark Added")
		return jsonify(valid=True, message="Remark Added")
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")

@app.route("/dashboard-sales/status-save-app",methods=["GET","POST"])
def status_save():
	#try:
	if request.method=="POST":
		data=request.json
		c_token=data["token"]
		r=data['remark']
		lead=Leads.query.filter_by(c_token=c_token).first()
		lead.lead_status=s
		lead.lead_status_remark=r
		db.session.commit()
		#flash("Remark Added")
		return jsonify(valid=True, message="Remark Added")
	else:
		return jsonify(valid=False,err="Method Not Allowed!!!")


if __name__ == '__main__':
	app.run(debug=True,host="0.0.0.0")