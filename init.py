from flask import Flask,render_template,redirect,url_for,request,jsonify,send_file,session,flash
from models import *
import uuid
import random
import string
from flask_mail import Mail,Message
from datetime import datetime,timedelta
from flask_marshmallow import Marshmallow
from passlib.hash import sha256_crypt
from functools import wraps
import json
import requests
from flask_migrate import Migrate
import base64
import io
import csv

app=Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:mom0511@localhost/leadsdb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
db.app=app

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='example@example.com'
app.config['MAIL_PASSWORD']='***********'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)

def pass_generator(size=8, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def get_token():
	token=""
	while True:
		token=pass_generator()
		x=User_details.query.filter_by(c_token=token).all()
		if len(x)==0:
			break
	return token

def send_sms(text,number):
  url = "http://enterprise.smsgupshup.com/GatewayAPI/rest"
  payload={
	  "method":"sendMessage",
	  "send_to":number,
	  "msg":text,
	  "msg_type":"TEXT",
	  "userid":8989898989,
	  "auth_scheme":"PLAIN",
	  "password":"dummy",
	  "format":"JSON"
	}
  response = requests.request("POST", url, data=payload)

def GetUserInfo():
	current_user=session["username"]
	data=User_details.query.filter_by(mobile_no=current_user).first()
	return data

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		try:
			if session["logged_in"]:
				return f(*args, **kwargs)
			else:
				return redirect("/get/login")
		except:
			return redirect("/get/login")
	return wrap

@app.route("/loginstatus",methods=["GET","POST"])
def loginstatus():
	if request.method=="POST":
		data = request.json
		c_token=data["token"]
		this_inf=User_details.query.filter_by(c_token=c_token).all()
		if len(this_inf)>0:
			return jsonify(valid=True)
		else:
			return jsonify(valid=False)

@app.route("/",methods=["GET","POST"])
def home():
	return redirect("/login")

@app.route("/login",methods=["GET","POST"])
def login():
	return render_template("login.html")

@app.route("/login1",methods=["GET","POST"])
def login1():
	# try:
	if request.method=="POST":
		user=User_details.query.filter_by(mobile_no=request.form["mob"]).all()
		if len(user)==0:
			new_user=User_details(mobile_no=request.form["mob"],c_token=get_token())
			db.session.add(new_user)
			db.session.commit()
			otp=random.randint(1000,9999)
			otp_obj=Otp_details(user_id=new_user.user_id,otp_no=otp,purpose=1,valid_till=datetime.now()+timedelta(minutes=5))
			db.session.add(otp_obj)
			db.session.commit()
			#send_sms("Your OTP for Login At XYZ is "+str(otp)+". Valid for 5 minutes.",request.form["mob"])
			return render_template("otp.html",uid=new_user.user_id,mob=new_user.mobile_no)
			#return jsonify(valid=True,token=new_c_token,updated=False)
		else:
			otp_no=Otp_details.query.filter_by(user_id=user[0].user_id).all()
			for ot in otp_no:
				db.session.delete(ot)
			db.session.commit()
			user[0].c_token=get_token()
			otp=random.randint(1000,9999)
			otp_obj=Otp_details(user_id=user[0].user_id,otp_no=otp,purpose=1,valid_till=datetime.now()+timedelta(minutes=5))
			db.session.add(otp_obj)
			db.session.commit()
			#send_sms("Your OTP for Login At XYZ is "+str(otp)+". Valid for 5 minutes.",request.form["mob"])
			return render_template("otp.html",uid=user[0].user_id,mob=user[0].mobile_no)
			#return jsonify(valid=True,token=user[0].c_token,updated=True)
	else:
		flash("Method Not Allowed...!!")
		return redirect("/login")
	# except:
	# 	return jsonify(valid=False,err="Something Went Wrong!!!")

@app.route("/verify/<int:uid>",methods=["GET","POST"])
def Verify(uid):
#	try:
	if request.method=="POST":
		otp=int(request.form["otp"])
		user_verify=Otp_details.query.filter_by(user_id=uid).first()
		if user_verify.valid_till>datetime.now() and user_verify.purpose==1 and user_verify.otp_no==otp:
			user=User_details.query.filter_by(user_id=uid).first()
			verified=True
			db.session.commit()
			db.session.delete(user_verify)
			db.session.commit()
			session['logged_in']=True
			session['username']=user.mobile_no
			if user.updated==True:
				if user.account_type==0:
					return redirect("/dashboard-channel")
				if user.account_type==1:
					return redirect("/dashboard-sales")
				if user.account_type==2:
					return redirect("/dashboard-manager")
				if user.account_type==3:
					return redirect("/dashboard-site-engineer")
				if user.account_type==4:
					return redirect("/dashboard-account-officer")
			else:
				return render_template("update_profile.html",uid=uid)
		else:
			flash("Wrong OTP or OTP Expired!!!")
			return redirect("/login")
	else:
		flash("Method Not Allowed")
		return redirect("/login")
	# except Exception as e:
	# 	return render_template("error.html",message="Some error occured!!!")

@app.route("/update-profile/<int:uid>",methods=["GET","POST"])
#@login_required
def update_profile(uid):
	if request.method=="POST":
		this_user=User_details.query.filter_by(user_id=uid).first()
		this_user.name=request.form["full_name"]
		this_user.email=request.form["email"]
		typee=request.form["account"]
		if typee=="designer":
			this_user.channel_partner_type=0
		if typee=="architect":
			this_user.channel_partner_type=1
		if typee=="individual":
			this_user.channel_partner_type=2
		if typee=="channel_partner":
			this_user.channel_partner_type=3
		this_user.updated=True
		this_user.cp_total_earning=0
		db.session.commit()
		if this_user.account_type==0:
			return redirect("/dashboard-channel")
		if this_user.account_type==1:
			return redirect("/dashboard-sales")
		if this_user.account_type==2:
			return redirect("/dashboard-manager")
		if this_user.account_type==3:
			return redirect("/dashboard-site-engineer")
		if this_user.account_type==4:
			return redirect("/dashboard-account-officer")
	else:
		flash("Something went wrong.")
		return redirect("/login")

@app.route("/logout",methods=["GET","POST"])
#@login_required
def logout():
	#try:
		mobile=session['username']
		session.pop('username',None)
		session['logged_in']=False
		flash("Successfully Logged Out.")
		return redirect("/login")
	# except:
	# 	flash("ALREADY LOGGED OUT")
	# 	return redirect("/login")

@app.route("/notifications",methods=["GET","POST"])
#@login_required
def notifications():
	#try:
		return render_template("notifications.html")




@app.route("/profileimageupdate",methods=["GET","POST"])
def profileimageupdate():
	if request.method=="POST":
		u=GetUserInfo()
		if u:
			# imgdata=base64.b64decode(data["imageData"])
			filename = 'profile'+str(u.user_id)+'.jpg'
			imageData=request.files['pfile'].read()
			with open('./static/images/'+filename, 'wb') as f:
				f.write(imageData)
			u.profile_picture=filename
			db.session.commit()
			flash("Profile Image Updated")
			return redirect("/profile")

@app.route("/get-image/<string:name>",methods=["GET","POST"])
def get_image(name):
  try:
    filename=name
    return send_file('./static/images/'+filename, mimetype='image')
  except:
    return send_file('./static/images/'+"profile.png", mimetype='image')


@app.route("/notification",methods=["GET","POST"])
def channel_notification_app():
	if request.method=="POST":
		this_user=GetUserInfo()
		#this_user=User_details.query.filter_by(c_token=c_tokken).first()
		result=[]
		for n in this_user.notif:
			result.append(n)
		return render_template("notification.html",result=result)



@app.route("/dashboard-channel",methods=["GET","POST"])
#@login_required
def dashboard_channel():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(channel_partner_id=user.user_id)
	earning=user.cp_total_earning
	active,pending,completed,rejected=0,0,0,0
	cp_name=["Designer","Architect","Individual","Channel Partner"]
	for lead in leads:
		if lead.lead_status_for_cp==1:
			active+=1
		elif lead.lead_status_for_cp==0:
			pending+=1
		elif lead.lead_status_for_cp==2:
			completed+=1
		elif lead.lead_status_for_cp==3:
			rejected+=1
	return render_template("dashboard_channel.html",name=user.name,cp_n=cp_name[user.channel_partner_type], earning=earning,active=active,pending=pending,completed=completed,rejected=rejected)

@app.route("/channel-activeleads",methods=["GET","POST"])
def channel_activeleads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(channel_partner_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_for_cp==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Active Leads",result=result,account_type=0)


@app.route("/channel-pendingleads",methods=["GET","POST"])
def channel_pendingleads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(channel_partner_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_for_cp==0:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Pending Leads",result=result,account_type=0)


@app.route("/channel-completedleads",methods=["GET","POST"])
def channel_completedleads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(channel_partner_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_for_cp==2:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Completed Leads",result=result,account_type=0)


@app.route("/channel-rejectedleads",methods=["GET","POST"])
def channel_rejectedleads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(channel_partner_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_for_cp==3:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Rejected Leads",result=result,account_type=0)

@app.route("/create-lead",methods=["GET","POST"])
def create_lead():
	return render_template("create_lead1.html")

@app.route("/create-lead1",methods=["GET","POST"])
def create_lead1():
	if request.method=="POST":
		this_user=GetUserInfo()
		client=Client_details(name=request.form["name"],mobile_number=request.form["mobile_number"])
		db.session.add(client)
		db.session.commit()
		lead=Leads(client_id=client.client_id,c_token=get_token())
		db.session.add(lead)
		db.session.commit()
		this_user.lead.append(lead)
		db.session.commit()
		#Assigning lead to sales having minimum pending leads
		all_sales=User_details.query.filter_by(account_type=1).all()
		user=all_sales[0]
		uid=user.user_id
		min=Leads.query.filter_by(sales_id=user.user_id,lead_status_by_sales=0).count()
		for user in all_sales:
			x=Leads.query.filter_by(sales_id=user.user_id,lead_status_by_sales=0).count()
			if x<min:
				min=x
				uid=user.user_id
		u=User_details.query.filter_by(user_id=uid).first()
		lead.sales_id=u.user_id
		lead.lead_status_by_sales=0
		#Assigning lead to manager having minimum unattended leads
		all_mngr=User_details.query.filter_by(account_type=2).all()
		user=all_mngr[0]
		uid=user.user_id
		min=Leads.query.filter_by(manager_id=user.user_id,lead_status_by_manager=0).count()
		for user in all_mngr:
			x=Leads.query.filter_by(manager_id=user.user_id,lead_status_by_manager=0).count()
			if x<min:
				min=x
				uid=user.user_id
		u=User_details.query.filter_by(user_id=uid).first()
		lead.manager_id=u.user_id
		lead.lead_status_by_manager=0
		lead.lead_status=1
		db.session.commit()
		#SEND NOTIFICATION TO SALES
		return render_template("create_lead2.html",client_id=client.client_id,lead_id=lead.lead_id)

@app.route("/create-lead2-page/<int:lead_id>/<int:client_id>",methods=["GET","POST"])
def create_lead2_page(client_id,lead_id):
	return render_template("create_lead2.html",client_id=client_id,lead_id=lead_id)

@app.route("/create-lead2/<int:lead_id>/<int:client_id>",methods=["GET","POST"])
def create_lead2(client_id,lead_id):
	# try:
	if request.method=="POST":
		user=GetUserInfo()
		email=request.form['email']
		address1=request.form['address1']
		address2=request.form['address2']
		city=request.form['city']
		state=request.form['state']
		pincode=request.form['pincode']
		enquiry_for=request.form['enquiry_for']
		package_type=request.form['package_type']
		client=Client_details.query.filter_by(client_id=client_id).first()
		if not client:
			flash("No Client Found")
			return redirect("/dashboard-channel")
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		if not lead:
			flash("No Lead Found")
			return redirect("/dashboard-channel")
		client.email=email
		client.address1=address1
		client.address2=address2
		client.city=city
		client.state=state
		client.pincode=pincode
		lead.enquiry_for=enquiry_for
		lead.package_type=package_type
		db.session.commit()
		flash("Lead Created Successfully")
		return redirect("/channel-home")
	else:
		flash("Method Not Allowed..!!!")
		return redirect("/channel-home")

@app.route("/profile",methods=["GET","POST"])
#@login_required
def profile():
	user=GetUserInfo()
	r=dict()
	s=["Channel Partner","Sales","Manager","Site Engineer","Account Ofiicer"]
	r['account_type']=s[user.account_type]
	r['channel_partner_type']=user.channel_partner_type
	r['name']=user.name
	r['mobile_no']=user.mobile_no
	r['email']=user.email
	r['pp']=user.profile_picture
	return render_template("profile.html",r=r)

@app.route("/claim-incentives-page",methods=["GET","POST"])
#@login_required
def claim_incentives_page():
	return render_template("channel_claim_incentive.html")

@app.route("/claim-incentives",methods=["GET","POST"])
#@login_required
def claim_incentives():
	# try:
	if request.method=="POST":
		user=GetUserInfo()
		company_name=request.form["company_name"]
		contact_person_name=request.form["contact_person_name"]
		contact_person_contact_no=request.form["contact_person_contact_no"]
		alternate_number=request.form["alternate_number"]
		upi_no=request.form["upi_no"]
		gst_no=request.form["gst_no"]
		pan_no=request.form["pan_no"]
		account_number=request.form["account_number"]
		ifsc=request.form["ifsc"]
		name=request.form["name"]
		bank=request.form["bank"]
		branch=request.form["branch"]
		c=Company_details(company_name=company_name,contact_person_name=contact_person_name,contact_person_contact_no=contact_person_contact_no,alternate_number=alternate_number,gst_no=gst_no,pan_no=pan_no,account_number=account_number,ifsc=ifsc,name=name,bank=bank,branch=branch)
		db.session.add(c)
		db.session.commit()
		user.company_id=c.company_id
		db.session.commit()
		flash("Successfully Applied for Claiming Incentives")
		return redirect("/channel-home")
	else:
		flash("Method not Allowed..!!")
		return redirect("/claim-incentives.html")
	# except:
	# 	return jsonify(valid=False,err=str(data))

@app.route("/update-bank-details-page",methods=["GET","POST"])
#@login_required
def update_bank_details_page():
	return render_template("channel_claim_incentive.html")

@app.route("/update-bank-details",methods=["GET","POST"])
#@login_required
def update_bank_details():
	# try:
	if request.method=="POST":
		user=GetUserInfo()
		c=Company_details.query.filter_by(company_id=user.company_id)
		upi_no=request.form["upi_no"]
		account_number=request.form["account_number"]
		ifsc=request.form["ifsc"]
		name=request.form["name"]
		bank=request.form["bank"]
		branch=request.form["branch"]
		c.upi_no=upi_no
		c.account_number=account_number
		c.ifsc=ifsc
		c.name=name
		c.bank=bank
		c.branch=branch
		db.session.commit()
		flash("Bank Details Updated Successfully")
		return redirect("/channel-home")
	else:
		flash("Something Went Wrong.")
		return redirect("/update_bank_details")
	# except:
	# 	return jsonify(valid=False,err=str(data))

@app.route("/channel-lead-details/<int:lead_id>",methods=["GET","POST"])
##@login_required
def client_details(lead_id):
	#try:
	#if request.method=="POST":
	lead=Leads.query.filter_by(lead_id=lead_id).first()
	client=Client_details.query.filter_by(client_id=lead.client_id).first()
	status=["Pending","Active","Completed","Rejected"]
	return render_template("channel_lead_details.html",client=client,lead=lead,status=status[lead.lead_status_for_cp])
	# else:
	# 	flash("Method Not Allowed!!!")
	# 	return redirect("/dashboard-channel")
	# except:
	# 	return jsonify(valid=False,err=str(data))

@app.route("/channel-home",methods=["GET","POST"])
#@login_required
def channel_home():
	#try:
	return render_template("home.html")





@app.route("/dashboard-sales",methods=["GET","POST"])
#@login_required
def dashboard_sales():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(sales_id=user.user_id).all()
	all,pending, Active, Negotiate, wip, Product_Ready, Completed, Dismissed=0,0,0,0,0,0,0,0
	for l in leads:
		if l.lead_status_by_sales==0 and l.lead_status==1:
			pending+=1
		if l.lead_status_by_sales==1 and l.lead_status==1:
			Active+=1
		if l.lead_status_by_sales==2 and l.lead_status==1:
			Negotiate+=1
		if l.lead_status_by_sales==3 and l.lead_status==1:
			Product_Ready+=1
		if l.lead_status_by_sales==4 and l.lead_status==1:
			Completed+=1
		if l.lead_status_by_sales==5 and l.lead_status==1:
			Dismissed+=1
		all+=1
	return render_template("dashboard_sales.html",name=user.name,pending=pending,Active=Active,Negotiate=Negotiate,wip=wip,Product_Ready=Product_Ready,Completed=Completed,Dismissed=Dismissed,all=all)


@app.route("/sales-pending-leads",methods=["GET","POST"])
def sales_pending_leads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(sales_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_sales==0 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Pending Leads",result=result,account_type=1)

@app.route("/sales-active-leads",methods=["GET","POST"])
def sales_active_leads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(sales_id=user.user_id).all()
	result=[]
	for lead in leads:
		if (lead.lead_status_by_sales==1  or lead.lead_status_by_sales==11) and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Active Leads",result=result,account_type=1)

@app.route("/sales-negotiate-leads",methods=["GET","POST"])
def sales_negotiate_leads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(sales_id=user.user_id).all()
	result=[]
	for lead in leads:
		if (lead.lead_status_by_sales==2  or lead.lead_status_by_sales==22) and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Negotiate Leads",result=result,account_type=1)

# @app.route("/sales-wip-leads",methods=["GET","POST"])
# def sales_wip_leads():
# 	user=GetUserInfo()
# 	leads=Leads.query.filter_by(sales_id=user.user_id).all()
# 	result=[]
# 	for lead in leads:
# 		if lead.lead_status_by_sales==3 and lead.lead_status==1:
# 			client=Client_details.query.filter_by(client_id=lead.client_id).first()
# 			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
# 	return render_template("lead_list.html",head="Work in Progress",result=result,account_type=1)

@app.route("/sales-product-ready-leads",methods=["GET","POST"])
def sales_product_ready_leads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(sales_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_sales==3 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Product Ready",result=result,account_type=1)

@app.route("/sales-completed-leads",methods=["GET","POST"])
def sales_completed_leads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(sales_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_sales==4 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Completed Leads",result=result,account_type=1)

@app.route("/sales-dismissed-leads",methods=["GET","POST"])
def sales_dismissed_leads():
	user=GetUserInfo()
	leads=Leads.query.filter_by(sales_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_sales==5 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Dismissed Leads",result=result,account_type=1)



@app.route("/sales-client-details/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_client_details(lead_id):
	#try:
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	client=Client_details.query.filter_by(client_id=lead.client_id).first()
	return render_template("sales_client_details.html",lead=lead,client=client,account_type=user.account_type)

@app.route("/sales-client-details-renegotiate/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_client_details_renegotiate(lead_id):
	#try:
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id).all()
	return render_template("sales_renegotiate.html",lead=lead,remarks=remarks,account="Sales")

@app.route("/sales-client-details-begin/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_client_details_begin(lead_id):
	#try:
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	lead.lead_status_for_cp=1
	lead.lead_status_by_sales=1
	lead.lead_status_by_manager=1
	client=Client_details.query.filter_by(client_id=lead.client_id).first()
	remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id).all()
	db.session.commit()
	if lead.welcome_call==False:
		return render_template("sales_welcome.html",lead_id=lead_id,head="Welcome Call",account="Sales",remarks=remarks)
	elif lead.welcome_email==False:
		return render_template("sales_welcome.html",lead_id=lead_id,head="Welcome Email",account="Sales",remarks=remarks)
	else:
		return render_template("sales_status.html",lead_id=lead_id,remarks=remarks)
	# else:
	# 	return render_template("sales_client_details.html",lead=lead,client=client)

#@app.route("/add-remark/<int:lead_id>",methods=["GET","POST"])
#@login_required
def add_remark(lead_id,remark):
	#try:
#	if request.method=="POST":
	user=GetUserInfo()
	rrr=remark
	r=str(user.name)+": "+rrr
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	rr=Remarks(lead_id=lead.lead_id,user_id=user.user_id,account_type=user.account_type,remark=r)
	db.session.add(rr)
	db.session.commit()
	lead.remarks.append(rr)
	db.session.commit()
	#flash("Remark Added")
	#return render_template("home.html")
	#return redirect(request.url)	#WHERE TO RETURN????


@app.route("/sales-welcome-call/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_welcome_call(lead_id):
	#try:
#	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
		remark=request.form["remark"]
		if(remark):
			add_remark(lead.lead_id,remark)
		lead.welcome_call=True
		db.session.commit()
		remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id).all()
		return render_template("sales_welcome.html",lead_id=lead_id,head="Welcome Email",account="Sales",remarks=remarks)
	# else:
	# 	flash("Something went wrong.")
	# 	return render_template("sales_welcome.html",lead_id=lead_id,head="Welcome Call",account="Sales")


@app.route("/sales-welcome-email/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_welcome_email(lead_id):
	#try:
#	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		remark=request.form["remark"]
		if(remark):
			add_remark(lead.lead_id,remark)
		lead.welcome_email=True
		db.session.commit()
		remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id).all()
		return render_template("sales_status.html",lead_id=lead_id,remarks=remarks)
	# else:
	# 	flash("Something went wrong")
	# 	return render_template("sales_welcome_email.html",lead_id=lead_id)


@app.route("/sales-status-save/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_status_save(lead_id):
	#try:
#	if request.method=="POST":
	user=GetUserInfo()
	s=request.form['status']
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	remark=request.form["remark"]
	if(remark):
		add_remark(lead.lead_id,remark)
	if s=='Dismissed':
		lead.lead_status_by_sales=5
		lead.lead_status_by_manager=5
		#IF LEAD DISMISSED, SEND NOTIFICATION TO MANAGER
		db.session.commit()
	if s=='in_progress':
		all_site=User_details.query.filter_by(account_type=3).all()
		user=all_site[0]
		uid=user.user_id
		min=Leads.query.filter_by(site_engineer_id=user.user_id,lead_status_by_site_engineer=0).count()
		for user in all_site:
			x=Leads.query.filter_by(site_engineer_id=user.user_id,lead_status_by_site_engineer=0).count()
			if x<min:
				min=x
				uid=user.user_id
		u=User_details.query.filter_by(user_id=uid).first()
		lead.site_engineer_id=u.user_id
		lead.lead_status_by_site_engineer=0
		lead.lead_status_by_sales=11
		db.session.commit()
	return render_template("home.html")
	# else:
	# 	flash("Something went Wrong.")
	# 	return render_template("sales_status.html")

@app.route("/sales-initial-offer-page/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_initial_offer_page(lead_id):
	#try:
#	if request.method=="POST":
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id).all()
	return render_template("sales_initial.html",lead=lead, remarks=remarks,account="Sales")


@app.route("/sales-initial-offer/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_initial_offer(lead_id):
	#try:
#	if request.method=="POST":
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	#remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id)
	lead.initial_offer=request.form["remark"]
	lead.lead_status_by_sales=22
	db.session.commit()

	#Assigning lead to account having minimum pending leads
	all_acc=User_details.query.filter_by(account_type=4).all()
	user=all_acc[0]
	uid=user.user_id
	min=Leads.query.filter_by(account_officer_id=user.user_id,lead_status_by_account_officer=1).count()
	for user in all_acc:
		x=Leads.query.filter_by(account_officer_id=user.user_id,lead_status_by_account_officer=1).count()
		if x<min:
			min=x
			uid=user.user_id
	u=User_details.query.filter_by(user_id=uid).first()
	lead.account_officer_id=u.user_id
	lead.lead_status_by_account_officer=1
	db.session.commit()

	return render_template("home.html")
	# else:
	# 	flash("Something went wrong")
	# 	return render_template("sales_initial_offer.html",lead_id=lead_id)


@app.route("/sales-installation-fix-page/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_installation_fix_page(lead_id):
	#try:
#	if request.method=="POST":
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id).all()
	return render_template("sales_initial.html",lead=lead, remarks=remarks,account="Sales")


@app.route("/sales-installation-fix/<int:lead_id>",methods=["GET","POST"])
#@login_required
def sales_installation_fix(lead_id):
	#try:
#	if request.method=="POST":
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	#remarks=Remarks.query.filter_by(lead_id=lead.lead_id,user_id=user.user_id)
	lead.install_date_remark=request.form["remark"]
	lead.lead_status_by_sales=4
	lead.lead_status_by_site_engineer=3
	db.session.commit()
	return render_template("home.html")







@app.route("/dashboard-manager",methods=["GET","POST"])
#@login_required
def dashboard_manager():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(manager_id=user.user_id).all()
	unattended,Active,Completed,Closed,Dismissed,Dismissed_by_Sales,m_all=0,0,0,0,0,0,0
	for l in leads:
		if l.lead_status_by_manager==0 and l.lead_status==1:
			unattended+=1
		if l.lead_status_by_manager==1 and l.lead_status==1:
			Active+=1
		if l.lead_status_by_manager==2 and l.lead_status==1:
			Completed+=1
		if l.lead_status_by_manager==3 and l.lead_status==1:
			Closed+=1
		if l.lead_status_by_manager==4 and l.lead_status==1:
			Dismissed+=1
		if l.lead_status_by_manager==5 and l.lead_status==1:
			Dismissed_by_Sales+=1
		m_all+=1		#all leads of that manager
	unattended=Leads.query.filter_by(lead_status_by_manager=0).count()
	return render_template("dashboard_manager.html",name=user.name,unattended=unattended,Active=Active,Completed=Completed,Closed=Closed,Dismissed=Dismissed,Dismissed_by_Sales=Dismissed_by_Sales,all=m_all)

@app.route("/manager-unattended",methods=["GET","POST"])
##@login_required
def manager_unattended():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(manager_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_manager==0:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Unattended By Sales",result=result,account_type=2)

@app.route("/manager-active",methods=["GET","POST"])
##@login_required
def manager_active():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(manager_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_manager==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Active Leads",result=result,account_type=2)

@app.route("/manager-completed",methods=["GET","POST"])
##@login_required
def manager_completed():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(manager_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_manager==2 or lead.lead_status_by_manager==22:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Completed Leads",result=result,account_type=2)


@app.route("/manager-closed",methods=["GET","POST"])
##@login_required
def manager_closed():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(manager_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_manager==3 or lead.lead_status_by_manager==33:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Closed Leads",result=result,account_type=2)


@app.route("/manager-dismissed",methods=["GET","POST"])
##@login_required
def manager_dismissed():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(manager_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_manager==4:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Dismissed Leads",result=result,account_type=2)

@app.route("/manager-dismissed-sales",methods=["GET","POST"])
##@login_required
def manager_dismissed_sales():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(manager_id=user.user_id).all()
	result=[]
	for lead in leads:
		if lead.lead_status_by_manager==5:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Dismissed by Sales",result=result,account_type=2)




@app.route("/manager-reject/<int:lead_id>",methods=["GET","POST"])
#@login_required
def manager_reject(lead_id):
	#try:
	# if request.method=="POST":
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id).first()
	lead.lead_status_for_cp=3
	lead.lead_status_by_manager=3
	lead.lead_status=3
	lead.manager_id=user.user_id
	db.session.commit()
	return redirect("/manager-unattended")

@app.route("/manager-approve/<int:lead_id>",methods=["GET","POST"])
#@login_required
def manager_approve(lead_id):
	#try:
	# if request.method=="POST":
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id).first()
	lead.lead_status_for_cp=0
	lead.lead_status_by_manager=1
	lead.lead_status=1
	lead.manager_id=user.user_id
	db.session.commit()
	result=[]
	all_user=User_details.query.filter_by(account_type=1).all()
	x=0
	for u in all_user:
		r=Leads.query.filter_by(sales_id=u.user_id,lead_status_by_sales=0,lead_status=1).all()
		if r:
			x=len(r)
		else:
			x=0
		result.append({"name":u.name,"uid":u.user_id,"pending_leads":x})
	return render_template("manager_select_sales.html",lead_id=lead.lead_id,result=result)
	# else:
	# 	flash("Method Not Allowed!!")
	# 	return redirect("/dashboard-manager")

@app.route("/manager-select-sales/<int:lead_id>/<int:uid>",methods=["GET","POST"])
#@login_required
def manager_select_sales(lead_id,uid):
	#try:
#	if request.method=="POST":
	user=User_details.query.filter_by(user_id=uid).first()
	lead=Leads.query.filter_by(lead_id=lead_id).first()
	lead.sales_id=user.user_id
	lead.lead_status_by_sales=0
	db.session.commit()
	#SEND NOTIFICATION TO SALES
	return render_template("manager_assigned_to.html",lead_id=lead.lead_id,sales_name=user.name,sales_id=user.user_id)
	# else:
	# 	flash("Method Not Allowed!!")
	# 	return redirect("/dashboard-manager")

@app.route("/manager-select-sales-skip/<int:lead_id>",methods=["GET","POST"])
#@login_required
def manager_select_sales_skip(lead_id):
	#try:
#	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		all_user=User_details.query.filter_by(account_type=1).all()
		user=all_user[0]
		uid=user.user_id
		min=Leads.query.filter_by(sales_id=user.user_id,lead_status_by_sales=0).count()
		for user in all_user:
			x=Leads.query.filter_by(sales_id=user.user_id,lead_status_by_sales=0).count()
			if x<min:
				min=x
				uid=user.user_id
		u=User_details.query.filter_by(user_id=uid).first()
		lead.sales_id=u.user_id
		lead.lead_status_by_sales=0
		db.session.commit()
		#SEND NOTIFICATION TO SALES
		return render_template("manager_assigned_to.html",lead_id=lead.lead_id,sales_name=u.name,sales_id=u.user_id)
	# else:
	# 	flash("Method Not Allowed!!")
	# 	return redirect("/dashboard-manager")

@app.route("/manager-lead-details/<int:lead_id>",methods=["GET","POST"])
#@login_required
def manager_lead_details(lead_id):
	#try:
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		client=Client_details.query.filter_by(client_id=lead.client_id).first()
		sales=User_details.query.filter_by(user_id=lead.sales_id).first()
		manager=User_details.query.filter_by(user_id=lead.manager_id).first()
		site_engineer=User_details.query.filter_by(user_id=lead.site_engineer_id).first()
		account_officer=User_details.query.filter_by(user_id=lead.account_officer_id).first()
		sales_status={'0':"Pending",'1':"Active",'11':"Site-engineer assigned",'2':"Negotiate",'22':"Negotiated",'3':"Product Ready",'4':"Completed",'5':"Dismissed"}
		manager_status={'0':"Unattended (by sales)",'1':"Active",'2':"Completed",'22':"Completed By Manager(Pay Channel Partner)",'3':"Closed",'4':"Dismissed",'5':"Dismissed by Sales"}
		site_engineer_status={'0':"Pending",'1':"Visit in Progress",'2':"Visited",'3':"To be Installed",'4':"Completed"}
		account_officer_status={'1':"Check Initial Payment",'11':"Initial Payment Received",'2':"Check Full Payment",'22':"Full Payment Received",'3':"Pay Channel Partner",'4':"Completed"}
		leadstatus={'0':"Pending",'1':"Active",'2':"Closed",'3':"Dismissed"}
		s_r=Remarks.query.filter_by(lead_id=lead_id,user_id=sales.user_id).all()
		m_r=Remarks.query.filter_by(lead_id=lead_id,user_id=manager.user_id).all()
		se_r=Remarks.query.filter_by(lead_id=lead_id,user_id=lead.site_engineer_id).all()
		ao_r=Remarks.query.filter_by(lead_id=lead_id,user_id=lead.account_officer_id).all()
		#return site_engineer.name
		return render_template("manager_lead_details.html",lead=lead,client=client,account_type=user.account_type,
		sales_name=sales.name if sales else "",sales_id=sales.user_id if sales else "",
		manager_name=manager.name if manager else "",manager_id=manager.user_id if manager else "",
		site_engineer_name=site_engineer.name if site_engineer else "",site_engineer_id=site_engineer.user_id if site_engineer else "",
		account_officer_name=account_officer.name if account_officer else "",account_officer_id=account_officer.user_id if account_officer else "",
		leadstatus=leadstatus,sales_status=sales_status,manager_status=manager_status,site_engineer_status=site_engineer_status,account_officer_status=account_officer_status,
		s_r=s_r,m_r=m_r,se_r=se_r,ao_r=ao_r)
	# except:
	# 	return redirect("/channel-home")


@app.route("/manager-save-remark/<int:lead_id>",methods=["GET","POST"])
#@login_required
def manager_save_remark(lead_id):
	#try:
	if request.method=="POST":
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		remark=request.form["remark"]
		if(remark):
			add_remark(lead_id,remark)
			flash("Remark Added")
		return redirect("/manager-lead-details/"+str(lead.lead_id))


@app.route("/manager-save-status/<int:lead_id>",methods=["GET","POST"])
#@login_required
def manager_save_status(lead_id):
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		s=request.form["status"]
		if s=="yes":
			lead.lead_status_by_manager=22
			lead.lead_status_by_account_officer=3
		if s=="no":
			lead.lead_status_by_manager=2
		db.session.commit()
		return render_template("home.html")
		#return redirect("/manager-lead-details/"+str(lead_id))


@app.route("/manager-change-lead-status/<int:lead_id>",methods=["GET","POST"])
#@login_required
def manager_change_lead_status(lead_id):
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		s=request.form["status"]
		if s=="Pending":
			lead.lead_status=0
		if s=="Active":
			lead.lead_status=1
		if s=="Closed":
			lead.lead_status=2
			lead.lead_status_by_manager=33
			lead.lead_status_for_cp=2
		if s=="Dismissed":
			lead.lead_status=3
		db.session.commit()
		return render_template("home.html")
		#return redirect("/manager-lead-details/"+str(lead_id))






@app.route("/dashboard-site-engineer",methods=["GET","POST"])
#@login_required
def dashboard_site_engineer():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(site_engineer_id=user.user_id)
	pending,vip,Visited,tbi,completed,allv=0,0,0,0,0,0
	for l in leads:
		if l.lead_status_by_site_engineer==0 and l.lead_status==1:
			pending+=1
		if l.lead_status_by_site_engineer==1 and l.lead_status==1:
			vip+=1
		if l.lead_status_by_site_engineer==2 and l.lead_status==1:
			Visited+=1
		if l.lead_status_by_site_engineer==3 and l.lead_status==1:
			tbi+=1
		if l.lead_status_by_site_engineer==4 and l.lead_status==1:
			completed+=1
		allv+=1
	return render_template("dashboard_site_engineer.html",name=user.name,pending=pending,vip=vip,Visited=Visited,tbi=tbi,completed=completed,all=allv)


@app.route("/site-engineer-pending",methods=["GET","POST"])
#@login_required
def site_engineer_pending():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(site_engineer_id=user.user_id,lead_status=1)
	result=[]
	for lead in leads:
		if lead.lead_status_by_site_engineer==0 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Pending Leads",result=result,account_type=3)


@app.route("/site-engineer-vip",methods=["GET","POST"])
#@login_required
def site_engineer_vip():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(site_engineer_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_by_site_engineer==1 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Visit in Progress",result=result,account_type=3)

@app.route("/site-engineer-visited",methods=["GET","POST"])
#@login_required
def site_engineer_visited():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(site_engineer_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_by_site_engineer==2 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Visited",result=result,account_type=3)

@app.route("/site-engineer-tbi",methods=["GET","POST"])
#@login_required
def site_engineer_tbi():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(site_engineer_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_by_site_engineer==3 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="To Be Installed",result=result,account_type=3)

@app.route("/site_engineer_complete",methods=["GET","POST"])
#@login_required
def site_engineer_complete():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(site_engineer_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_by_site_engineer==4 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",head="Completed Leads",result=result,account_type=3)

@app.route("/site_engineer_allv",methods=["GET","POST"])
#@login_required
def site_engineer_allv():
	#try:
	results=Leads.query.filter_by(site_engineer_id=user.user_id)
	return render_template("site_engineer_allv.html",result=result)


@app.route("/site-engineer-lead-details/<int:lead_id>",methods=["GET","POST"])
#@login_required
def site_engineer_lead_details(lead_id):
	#try:
#	if request.method=="POST":
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	client=Client_details.query.filter_by(client_id=lead.client_id).first()
	return render_template("sales_client_details.html",lead=lead,client=client,account_type=user.account_type)
	# else:
	# 	flash("Method Not Allowed!!")
	# 	return redirect("/dashboard_site_engineer")

@app.route("/site-engineer-save-status-page/<int:lead_id>",methods=["GET","POST"])
#@login_required
def site_engineer_save_status_page(lead_id):
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	remarks=Remarks.query.filter_by(lead_id=lead_id,user_id=user.user_id).all()
	client=Client_details.query.filter_by(client_id=lead.client_id).first()
	return render_template("site-engineer-status.html",remarks=remarks,lead=lead,client=client,account_type=user.account_type)

@app.route("/site-engineer-save-status1/<int:lead_id>",methods=["GET","POST"])
#@login_required
def site_engineer_save_status1(lead_id):
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		r=request.form["status"]
		remark=request.form["remark"]
		if(remark):
			add_remark(lead_id,remark)
		if r=='vip':
			lead.lead_status_by_site_engineer=1
		if r=='Visited':
			lead.lead_status_by_site_engineer=2
			lead.lead_status_by_sales=2
		db.session.commit()
		return render_template("home.html")
	# else:
	# 	flash("Method Not Allowed!!")
	# 	return redirect("/site-engineer-lead-details/"+str(lead_id))

@app.route("/site-engineer-save-status2/<int:lead_id>",methods=["GET","POST"])
#@login_required
def site_engineer_save_status2(lead_id):
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		r=request.form["status"]
		remark=request.form["remark"]
		if request.file['filee']:
			filee=request.file['filee'].read()
			file_save(lead.lead_id,filee)
		if remark:
			add_remark(lead_id,remark)
		if r=='noins':
			lead.lead_status_by_site_engineer=3
		if r=='ins':
			lead.lead_status_by_site_engineer=4
			lead.lead_status_by_account_officer=2
		db.session.commit()
		return render_template("home.html")
	# else:
	# 	flash("Method Not Allowed!!")
	# 	return redirect("/site-engineer-lead-details/"+str(lead_id))

def file_save(lead_id,imageData):
	filename = 'feedback'+str(lead_id)+'.jpg'
	# imageData=request.files['pfile'].read()
	with open('./static/images/'+filename, 'wb') as f:
		f.write(imageData)
	# u.profile_picture=filename
	# db.session.commit()






@app.route("/dashboard-account-officer",methods=["GET","POST"])
#@login_required
def dashboard_account_officer():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(account_officer_id=user.user_id)
	cip,cfp,pcp,completed=0,0,0,0
	for l in leads:
		if l.lead_status_by_account_officer==1 and l.lead_status==1:
			cip+=1
		if l.lead_status_by_account_officer==2 and l.lead_status==1:
			cfp+=1
		if l.lead_status_by_account_officer==3 and l.lead_status==1:
			pcp+=1
		if l.lead_status_by_account_officer==4 and l.lead_status==1:
			completed+=1
	return render_template("dashboard_account_officer.html",name=user.name,cip=cip,cfp=cfp,pcp=pcp,completed=completed)


@app.route("/account-officer-cip",methods=["GET","POST"])
#@login_required
def account_officer_cip():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(account_officer_id=user.user_id)
	result=[]
	for lead in leads:
		if (lead.lead_status_by_account_officer==1 or lead.lead_status_by_account_officer==11) and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",result=result,head="Check Initial Payment",account_type=4)


@app.route("/account-officer-cfp",methods=["GET","POST"])
#@login_required
def account_officer_cfp():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(account_officer_id=user.user_id)
	result=[]
	for lead in leads:
		if (lead.lead_status_by_account_officer==2 or lead.lead_status_by_account_officer==22) and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",result=result,head="Check Final Payment",account_type=4)

@app.route("/account-officer-pcp",methods=["GET","POST"])
#@login_required
def account_officer_pcp():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(account_officer_id=user.user_id)
	result=[]
	for lead in leads:
		if (lead.lead_status_by_account_officer==3 or lead.lead_status_by_account_officer==33) and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",result=result,head="Pay Channel Partner",account_type=4)

@app.route("/account-officer-completed",methods=["GET","POST"])
#@login_required
def account_officer_completed():
	#try:
	user=GetUserInfo()
	leads=Leads.query.filter_by(account_officer_id=user.user_id)
	result=[]
	for lead in leads:
		if lead.lead_status_by_account_officer==4 and lead.lead_status==1:
			client=Client_details.query.filter_by(client_id=lead.client_id).first()
			result.append({"lead":lead,"lead_id":lead.lead_id,"date":lead.generation_date,"name":client.name,"city":client.city})
	return render_template("lead_list.html",result=result,head="Completed Leads",account_type=4)



@app.route("/account-officer-lead-details/<int:lead_id>",methods=["GET","POST"])
#@login_required
def account_officer_lead_details(lead_id):
	#try:
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id,lead_status=1).first()
	client=Client_details.query.filter_by(client_id=lead.client_id).first()
	return render_template("sales_client_details.html",lead=lead,client=client,account_type=user.account_type)

@app.route("/account-officer-cp-page/<int:lead_id>",methods=["GET","POST"])
#@login_required
def account_officer_cp_page(lead_id):
	#try:
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id).first()
	cpname=lead.user.name
	mob=lead.user.mobile_no
	company=Company_details.query.filter_by(company_id=lead.user.company_id).first()
	return render_template("account_cp_details.html",lead=lead,name=cpname,mob=mob,c=company)

@app.route("/account-officer-save-status-page/<int:lead_id>",methods=["GET","POST"])
#@login_required
def account_officer_save_status_page(lead_id):
	#try:
	user=GetUserInfo()
	lead=Leads.query.filter_by(lead_id=lead_id).first()
	remarks=Remarks.query.filter_by(lead_id=lead_id,user_id=user.user_id)
	if lead.lead_status_by_account_officer==3:
		cpname=lead.user.name
		mob=lead.user.mobile_no
		company=Company_details.query.filter_by(company_id=lead.user.company_id).first()
		return render_template("account_officer_status.html",lead=lead,name=cpname,mob=mob,c=company)
	else:
		client=Client_details.query.filter_by(client_id=lead.client_id).first()
		return render_template("account_officer_status.html",lead=lead,client=client,remarks=remarks)

@app.route("/account-officer-cip-save/<int:lead_id>",methods=["GET","POST"])
#@login_required
def account_officer_cip_save(lead_id):
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		#amount=request.form['amount']
		status=request.form["status"]
		remark=request.form["remark"]
		if(remark):
			add_remark(lead_id,remark)
		if status=='paid':
			lead.lead_status_by_account_officer=11
			#lead.installments=lead.installments+str(amount)+","
		if status=='not_paid':
			lead.lead_status_by_account_officer=1
		db.session.commit()
		return render_template("home.html")

@app.route("/account-officer-cfp-save/<int:lead_id>",methods=["GET","POST"])
#@login_required
def account_officer_cfp_save(lead_id):
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		#amount=request.form['amount']
		status=request.form["status"]
		remark=request.form["remark"]
		if(remark):
			add_remark(lead_id,remark)
		if status=='paid':
			lead.lead_status_by_account_officer=22
			#lead.installments=lead.installments+str(amount)+","
			lead.lead_status_by_manager=2
		if status=='not_paid':
			lead.lead_status_by_account_officer=2
		db.session.commit()
		return render_template("home.html")

@app.route("/account-officer-pcp-save/<int:lead_id>",methods=["GET","POST"])
#@login_required
def account_officer_pcp_save(lead_id):
	#try:
	if request.method=="POST":
		user=GetUserInfo()
		lead=Leads.query.filter_by(lead_id=lead_id).first()
		#amount=request.form['amount']
		status=request.form["status"]
		remark=request.form["remark"]
		if(remark):
			add_remark(lead_id,remark)
		if status=='paid':
			lead.lead_status_by_account_officer=4
			lead.lead_status_by_manager=3
			#lead.installments=lead.installments+str(amount)+","
		if status=='not_paid':
			lead.lead_status_by_account_officer=3
		db.session.commit()
		return render_template("home.html")





app.secret_key="pta nhi secret key kyu janani hai"

if __name__ == '__main__':
	app.run(debug=True,host="0.0.0.0")
