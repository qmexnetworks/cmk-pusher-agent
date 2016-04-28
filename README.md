# CMK Pusher
CMK Pusher is a passive push agent extension for Check_MK. At the moment it only supports Linux, but Windows
Support is planned and was the Reason for this Project.

It uses a PHP JSON API for Communication. If setup correctly all communication will use HTTPS so all Data is SSL Encrypted.
Also its possible to use Client based compression.

##### Installation API (Check_MK Server side)
- Copy the api Directory to your Check_MK Server in the Webserver root directory. (eg. /var/www/html)
- You need PHP Support on your Webserver
- Edit config.inc.php to your needs and create the Spool Directory with the necessary permissions (eg. /opt/cmk-pusher/spool)

##### Installation Linux Agent
- You need the Check_MK Agent installed and you need Python 2.7 and PyCurl Support
- Copy all Files from agent/Linux to a Directory on you Linux Server you want to Monitor (eg. /opt/cmk-pusher)
- Edit the config.ini (Password needs to be the same on the two sides), configure the Client Name (needs to be exactly the same as the configured Host in Check_MK, dont use special characters or whitespaces)
- Create a Cron Entry, the Check_MK Agent needs to be executed as root, add the cron.sh to your crontab to run every Minute

##### Installation Windows Agent (more than Beta at the moment) - Option 1 Python Way
- Install the Check_MK Agent (you dont have to install it as service)
- Install Python 2.7 under Windows (and let it add to the PATH)
- Open cmd and Install two packets via pip:
```
pip install pycurl
pip install pypiwin32
```
- Open cmd as an Administrator an do postinstall
```
cd C:\Python27
python scripts\pywin32_postinstall.py -install
```
- Install it as Service, open cmd as Administrator and run:
```
python C:\Install\cmk-pusher-agent.py install
```
- Know you can start and edit the service in the services.msc
- Service will push data every 30 seconds

##### Installation Windows Agent (more than Beta at the moment) - Option 2 EXE Way
- Install the Check_MK Agent (you dont have to install it as service)
- Unpack cmk-pusher-agent.zip to eg. C:\Install
- At the moment, the Config file must be in C:\Install\cmk-agent-pusher\
- Edit the config.ini (Password needs to be the same on the two sides), configure the Client Name (needs to be exactly the same as the configured Host in Check_MK, dont use special characters or whitespaces)
- Edit SERVERHOSTNAME in config.ini it should comply with your SSL Certificate
- Install Service, run cmd as Administrator and run the following command:
```
c:\Install\cmk-pusher-agent\cmk-pusher-agent.exe
```
- Service will push data every 30 seconds

##### Check_MK Configuration
The easiest way is to create a new tag. For example under agent you can add CMK Pusher withe the tag cmk-pusher.
Now add a Datasource Program (eg. in WATO under Individual program call instead of agent access) and add the following line:
```
cat /opt/cmk-pusher/spool/<HOST>.dump
```
At the moment this is a very cheap Solution and will be extended eg. with Freshness Check in the near Future.
After a few Minutes you should have Data in Check_MK for a Service Discovery.

For Windows Agents you should create a Rule for "System Time" and extend the times for Warning and Critical