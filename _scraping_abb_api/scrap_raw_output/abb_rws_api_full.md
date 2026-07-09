# ABB Robot Web Services — API Reference

> 555 routes documentées

---

## Root Resource

**Chemin :** Root Resource

---

## Get Service list

**Chemin :** Root Resource › Get Service list

URL — /

**URL :** `/`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
srvlst-service-li
The RobotWare service
ctrl = controller resource
rw = robotware resource
progress = progress resource
fileservice = fileservice resource
users = users resource
subscription = subscription resource
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/"
```

**Notes :** Supported in bootserver mode

---

## Logout

**Chemin :** Root Resource › Logout

URL — /logout

**URL :** `/logout`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/logout"
```

**Notes :** Supported in bootserver mode

---

## Subscription Service

**Chemin :** Subscription Service

---

## Get Subscription Actions

**Chemin :** Subscription Service › Get Subscription Actions

URL — /subscription

**URL :** `/subscription`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
subscribe
resources
=[numeric]
Required
, the subscription resource identifier
*<identifier>=[alphanumeric]
Required
, the resource URI
*<identifier>-p=[numeric]
Required
, the priority associated with the susbcription resource
sub-resource
the subscription resource
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/subscription?action=show"
```

**Notes :** The form body is in standard form data format and consists of three name-value pairs per resource.
1st pair - resources=<identifier> e.g. resources=1
2nd pair - <identifier>=<subscription-resource> e.g. 1=/rw/iosystem/signals/Virtual1/Board1/do1;state
3rd pair - <identifier>-p=<0|1|2> 1-p=1
In the above, <identifier> can be any value but it is recommended to use integer values such as 1, 2,3 etc. An example payload to subscribe on a single resource "/rw/iosystem/signals/Virtual1/Board1/do1;state" and associate priority "1" to the resource is shown below:
resources=1&1=/rw/iosystem/signals/Virtual1/Board1/do1;state&1-p=1
Similarly, the payload for subscribing on two resources
"/rw/iosystem/signals/Virtual1/Board1/do1;state" and "/rw/iosystem/signals/Virtual1/Board1/do2;state"
resources=1&1=/rw/iosystem/signals/Virtual1/Board1/do1;state&1-p=1& resources=2&2=/rw/iosystem/signals/Virtual1/Board1/do2;state&2-p=0
maximum 1000 resources can be subscribed per group
Not supported in bootserver mode

---

## Subscribe on resources

**Chemin :** Subscription Service › Subscribe on resources

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**Data Params :**
```
resources
= An identifier
Required
*<identifier>*= The subscription resource URI
Required
*<identifier>-p*= The priority associated with the subscription resource.
Required
'0' for Low priority    (Valid for all resources)
 '1' for Medium priority (Valid for all resources)
 '2' for High priority   (Valid for only 'IOSIGNALS' and 'RAPID Persistent variable value' resources)
```

**Resources :**
```
ios-signalstate-ev
lstate
Signals state {blocked | unblocked}
lvalue
Logical Signal value
```

**Success :** CREATED(201), see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415) See
Robot controller return codes

**Sample Call :**
```bash
Low Priority subscription
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/signals/Virtual1/Board1/di1;state&1-p=0&resources=2&2=/rw/iosystem/signals/Virtual1/Board1/di2;state&2-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/ctrlstate&1-p=0" -X POST "http://localhost/subscription"
Medium Priority subscription
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/signals/Virtual1/Board1/di1;state&1-p=1&resources=2&2=/rw/iosystem/signals/Virtual1/Board1/di2;state&2-p=1" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/rapid/symbol/data/RAPID/T_ROB1/uimsg/PNum;value&1-p=1" "http://localhost/subscription"
High Priority subscription
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/signals/Virtual1/Board1/di1;state&1-p=2&resources=2&2=/rw/iosystem/signals/Virtual1/Board1/di2;state&2-p=2" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/rapid/symbol/data/RAPID/T_ROB1/uimsg/PNum;value&1-p=2" "http://localhost/subscription"
```

**Notes :** The sequence of steps involved to setup subscription and start listening for events are shown below:
Subscribe on resources
Response to this HTTP request is a list of initial events for the subscribed resources along with the location header.
Retrieve Location header and use this value to setup web socket connection
Receive events and parse the events
Maximum 1000 resources can be subscribed per group with low priotity and medium priority
Each client can have maximum 2 groups.
Low priority subscription(p=0) and Medium priority subscription(p=1) is allowed on any resource.
RobotWebservice clients can subscribe maximum of 64 resources with High priority (p=2).
High priority subscription is allowed only on below two types of resources.
1.IOSignals in IOSYSTEM.
2.Rapid Persistentvariables in RAPID.
Not supported in bootserver mode

---

## Operations on Subscription Group

**Chemin :** Subscription Service › Operations on Subscription Group

---

## Get Subscription Group Actions

**Chemin :** Subscription Service › Operations on Subscription Group › Get Subscription Group Actions

URL — /subscription/{group-id}

**URL :** `/subscription/{group-id}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
unsubscribe-group
None
unsubscribe-resource
None
update-group
resources
=[numeric]
Required
, the subscription resource identifier
*<identifier>=[alphanumeric]
Required
, the resource URI
*<identifier>-p=[numeric]
Required
, the new priority associated with the susbcription resource
update-resource-priority
resources
=[numeric]
Required
, the subscription resource identifier
*<identifier>=[alphanumeric]
Required
, the resource URI
*<identifier>-p=[numeric]
Required
, the new priority associated with the susbcription resource
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/subscription/1?action=show"
```

**Notes :** The form body is in standard form data format and consists of three name-value pairs per resource.
1st pair - resources=<identifier> e.g. resources=1
2nd pair - <identifier>=<subscription-resource> e.g. 1=/rw/iosystem/signals/Virtual1/Board1/do1;state
3rd pair - <identifier>-p=<0|1|2> 1-p=1
In the above, <identifier> can be any value but it is recommended to use integer values such as 1, 2,3 etc.
An example payload to subscribe on a single resource "/rw/iosystem/signals/Virtual1/Board1/do1;state" and associate priority "2" (High priority subscription) to the resource is shown below:
resources=1&1=/rw/iosystem/signals/Virtual1/Board1/do1;state&1-p=2
Similarly, the payload for subscribing on two resources (first resource on Medium priority and second resource on Low priority subscription)
"/rw/iosystem/signals/Virtual1/Board1/do1;state" and "/rw/iosystem/signals/Virtual1/Board1/do2;state"
resources=1&1=/rw/iosystem/signals/Virtual1/Board1/do1;state&1-p=1& resources=2&2=/rw/iosystem/signals/Virtual1/Board1/do2;state&2-p=0
maximum 1000 resources can be subscribed per group
Not supported in bootserver mode

---

## Add new resources, Remove existing Resources or change existing resources priorities.

**Chemin :** Subscription Service › Operations on Subscription Group › Add new resources, Remove existing Resources or change existing resources priorities.

URL — /subscripion/{group-id}

**URL :** `/subscripion/{group-id}`  
**Method :** `PUT`

**URL Params :**
```
None
```

**Data Params :**
```
update-resource-priority
resources
= An identifier
Required
*<identifier>*= The subscription resource URI
Required
*<identifier>-p*= The priority associated with the subscription resource.
Required
update-group
resources
= An identifier
Required
*<identifier>*= The subscription resource URI
Required
*<identifier>-p*= The priority associated with the subscription resource.
Required
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Update resources in Subscription group.
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/signals/Virtual1/Board1/di1;state&1-p=0&resources=2&2=/rw/iosystem/signals/Virtual1/Board1/di2;state&2-p=1" -X PUT "http://localhost/subscription/1"
```

**Notes :** maximum 1000 resources can be subscribed per group
Each client can have maximum 2 groups.
Low priority subscription(p=0) is allowed on any resource.
Medium priority subscription(p=1) is allowed on any resource.
RobotWebservice clients can subscribe maximum of 64 resources with High priority (p=2).
High priority subscription is allowed only on below two types of resources.
1.IOSignals in IOSYSTEM.

2.RapidPersistentvariables in RAPID.
Not supported in bootserver mode

---

## Unsubscribe or remove the subscription group/resources in group.

**Chemin :** Subscription Service › Operations on Subscription Group › Unsubscribe or remove the subscription group/resources in group.

URL — /subscripion/{group-id}

**URL :** `/subscripion/{group-id}`  
**Method :** `DELETE`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Unsubscribe or remove subscription group.
curl --digest -u "Default User":robotics -X DELETE "http://localhost/subscription/1"
Unsubscribe or remove subscription resource from the group.
curl --digest -u "Default User":robotics -X DELETE "http://localhost/subscription/1/rw/iosystem/signals/Virtual1/Board1/di1;state"
```

**Notes :** Not supported in bootserver mode

---

## Operations on Subscription Resource

**Chemin :** Subscription Service › Operations on Subscription Group › Operations on Subscription Resource

---

## Unsubscribe or remove the resource from subscription group.

**Chemin :** Subscription Service › Operations on Subscription Group › Operations on Subscription Resource › Unsubscribe or remove the resource from subscription group.

URL — /subscripion/{group-d}/{resource-uri}

**URL :** `/subscripion/{group-d}/{resource-uri}`  
**Method :** `DELETE`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Unsubscribe or remove subscription resource from subscription group.
curl --digest -u "Default User":robotics -X DELETE "http://localhost/subscription/1/rw/iosystem/signals/Virtual1/Board1/di1;state"
```

**Notes :** Not supported in bootserver mode

---

## User Service

**Chemin :** User Service

---

## Get User Resources

**Chemin :** User Service › Get User Resources

URL — /users

**URL :** `/users`  
**Method :** `GET`

**URL Params :**
```
user-type=self
Optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
user
title
represents name of the user.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/users"
```

**Notes :** Supported in bootserver mode

---

## Get User Actions

**Chemin :** User Service › Get User Actions

URL — /users

**URL :** `/users`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
register
application
=[appName]
Required
,
username
=[UserName]
Required
,
location
=[place]
Required
,
ulocale
=[local|remote]
Required
,
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/users?action=show"
```

**Notes :** Supported in bootserver mode

---

## Register the user

**Chemin :** User Service › Register the user

URL — /users

**URL :** `/users`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
username
= The username to register. It represents user alias name.
Required
application
= The application name to register
Required
location
= The location of the user
Required
ulocale
= local or remote user
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Register user
curl --digest -u "Default User":robotics -d "username=xyz&application=RobotStudio&location=IN-BLR-XXXX&ulocale=remote" -X POST "http://localhost/users"
```

**Notes :** Supported in bootserver mode.
Given username, application and location are used only as free-text information.
User can be registered as local client (ulocale=local) only if the request comes from service port or the TPU port.

---

## Impersonate a user

**Chemin :** User Service › Impersonate a user

URL — /users

**URL :** `/users`  
**Method :** `POST`

**URL Params :**
```
action=impersonate
Required
See
Common URL parameters
```

**Data Params :**
```
uid
= The uas uid of the user to be impersonated.
Required
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
Register user
curl --digest -u "Default User":robotics -d "uid=11" -X POST "http://localhost/users?action=impersonate"
```

**Notes :** Supported in bootserver mode

---

## Login as Local User

**Chemin :** User Service › Login as Local User

URL — /users

**URL :** `/users`  
**Method :** `POST`

**URL Params :**
```
action=set-locale
Required
See
Common URL parameters
```

**Data Params :**
```
type={local|remote}
Required
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** CONFLICT(409) : if the user has already logged in as remote or local client and sets the type as remote or local respectively.
FORBIDDEN(403) : if the user does not toggle the enabling button within 5 seconds.
BAD_REQUEST(400) : if the user has sent invalid values for type.
See
Robot controller return codes

**Sample Call :**
```bash
Login as local user
curl --digest -u "Default User":robotics -d "type=local" -X POST "http://localhost/users?action=set-locale"
```

**Notes :** Supported in bootserver mode

---

## Operations on Users grants

**Chemin :** User Service › Operations on Users grants

---

## Get User grants

**Chemin :** User Service › Operations on Users grants › Get User grants

URL — /users/grants

**URL :** `/users/grants`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
user-grant
title
represents name of the usergrant.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/users/grants"
```

**Notes :** Supported in bootserver mode

---

## Operations on RMMP

**Chemin :** User Service › Operations on RMMP

---

## Get RMMP state

**Chemin :** User Service › Operations on RMMP › Get RMMP state

URL — /users/rmmp

**URL :** `/users/rmmp`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Resources :**
```
userid
User id
alias
Alias for the user. For users on a Windows PC it is the Windows user name.
location
User location. For users on a PC it is the PC's network name.
application
Name of the application the user is using. E.g., "RobotStudio-Online", "PickMaster"
privilege
{none|pending modify|modify|exec}
rmmpheldbyme
{true | false} whether the rmmp request and the current request are mady by same user.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
Get RMMP state
curl --digest -u "Default User":robotics "http://localhost/users/rmmp"
```

**Notes :** Not Supported in bootserver mode

---

## Get RMMP Actions

**Chemin :** User Service › Operations on RMMP › Get RMMP Actions

URL — /users/rmmp

**URL :** `/users/rmmp`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/users/rmmp?action=show"
```

**Notes :** Not Supported in bootserver mode

---

## Request RMMP

**Chemin :** User Service › Operations on RMMP › Request RMMP

URL — /users/rmmp

**URL :** `/users/rmmp`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
privilege
={modify|exec}
Required
```

**Success :** ACCEPTED(202)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Grant RMMP
curl --digest -u "Default User":robotics -d "privilege=modify" -X POST "http://localhost/users/rmmp"
```

**Notes :** Not Supported in bootserver mode

---

## Grant or deny an RMMP request

**Chemin :** User Service › Operations on RMMP › Grant or deny an RMMP request

URL — /users/rmmp

**URL :** `/users/rmmp`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
See
Common URL parameters
```

**Data Params :**
```
uid
= The uas uid of the user who made the request for rmmp
Required
privilege
={modify|exec|deny}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Grant RMMP
curl --digest -u "Default User":robotics -d "uid=11&privilege=modify" -X POST "http://localhost/users/rmmp?action=set"
```

**Notes :** Not Supported in bootserver mode

---

## Cancel held or requested RMMP

**Chemin :** User Service › Operations on RMMP › Cancel held or requested RMMP

URL — /users/rmmp

**URL :** `/users/rmmp`  
**Method :** `POST`

**URL Params :**
```
action=cancel
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Sample Call :**
```bash
Cancel held rmmp
curl --digest -u "Default User":robotics -X POST "http://localhost/users/rmmp?action=cancel"
```

**Notes :** Not Supported in bootserver mode

---

## Subscribe on RMMP Request event

**Chemin :** User Service › Operations on RMMP › Subscribe on RMMP Request event

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/users/rmmp')
Required
<identifier>-p = The priority associated with the subscription resource.
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/users/rmmp&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/users/rmmp&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode.

---

## Poll for RMMP grant status

**Chemin :** User Service › Operations on RMMP › Poll for RMMP grant status

URL — /users/rmmp/poll

**URL :** `/users/rmmp/poll`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
poll for rmmp status
curl --digest -u "Default User":robotics "http://localhost/users/rmmp/poll"
```

**Notes :** Not Supported in bootserver mode

---

## Operations on Remote User

**Chemin :** User Service › Operations on Remote User

---

## Get remote user actions

**Chemin :** User Service › Operations on Remote User › Get remote user actions

URL — /users/remoteuser

**URL :** `/users/remoteuser`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400), FORBIDDEN(403), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/users/remoteuser?action=show"
```

**Notes :** Not Supported in bootserver mode

---

## Remote User Logon Request

**Chemin :** User Service › Operations on Remote User › Remote User Logon Request

URL — /users/remoteuser

**URL :** `/users/remoteuser`  
**Method :** `POST`

**URL Params :**
```
action=remotelogin
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD REQUEST(400), FORBIDDEN(403), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/users/remoteuser?action=remotelogin"
```

**Notes :** Not Supported in bootserver mode.
The UAS grant UAS_REMOTE_LOGIN is required.

---

## Remote User Logout Request

**Chemin :** User Service › Operations on Remote User › Remote User Logout Request

URL — /users/remoteuser

**URL :** `/users/remoteuser`  
**Method :** `POST`

**URL Params :**
```
action=remotelogout
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD REQUEST(400), FORBIDDEN(403), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/users/remoteuser?action=remotelogout"
```

**Notes :** Not Supported in bootserver mode

---

## Subscribe on remote user state

**Chemin :** User Service › Operations on Remote User › Subscribe on remote user state

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/users/remoteuser')
Required
<identifier>-p = The priority associated with the subscription resource.
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/users/rmmp&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/users/rmmp&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode.

---

## Controller Service

**Chemin :** Controller Service

---

## Get Controller Resources

**Chemin :** Controller Service › Get Controller Resources

URL — /ctrl

**URL :** `/ctrl`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-clock-info
datetime
The current system time in
YYYY-MM-DD T HH:MM:SS
format.
ctrl-identity-info
ctrl-name
Alphanumeric, the name, ID, type (RC or VC), MAC address and level (system or boot level) of the controller.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl"
```

**Notes :** Supported in bootserver mode

---

## Get Controller Actions

**Chemin :** Controller Service › Get Controller Actions

URL — /ctrl

**URL :** `/ctrl`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
ctrl-restart
restart-mode
=[restart|shutdown|xstart]
Required
, - Multiple selection
restart
- The controller will be restarted. The state is saved and any changed system parameter settings will be activated after the restart.
shutdown
- The main computer will be shut down. Should be used if the controller UPS is broken.
xstart
- The controller will be restarted and the Boot Application will be started. The current system is saved and deactivated (the controller is non-functional, for advanced maintenance only).
istart
- The controller will be restarted with the original installation settings
pstart
- The controller will be restarted and reset the RAPID
bstart
- The controller will be restarted and revert to last automatically saved state
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl?action=show"
```

**Notes :** Supported in bootserver mode

---

## Get Controller environment variable

**Chemin :** Controller Service › Get Controller environment variable

URL — /ctrl/${ENVNAME}

**URL :** `/ctrl/${ENVNAME}`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-env
The value associated with the specified environment variable.
```

**Success :** HTTP_OK(200)

**Error :** NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics " http://localhost/ctrl/$TEMP "
```

---

## Restart or Shutdown controller

**Chemin :** Controller Service › Restart or Shutdown controller

URL — /ctrl

**URL :** `/ctrl`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
restart-mode
={ restart|xstart|shutdown|istart|pstart|bstart }
Required
where
restart
: The controller will be restarted. The state is saved and any changed system parameter settings will be activated after the restart.
shutdown
: The main computer will be shut down. Should be used if the controller UPS is broken.
xstart
: The controller will be restarted and the Boot Application will be started. The current system is saved and deactivated (the controller is non-functional, for advanced maintenance only).
istart
: The controller will be restarted. The current system parameter settings and RAPID programs will be discarded, and the original system installation settings will be used.
pstart
: The controller will be restarted. The current RAPID programs and data will be discarded but not the system parameter settings.
bstart
: The controller will be restarted. The last automatically saved system state will be loaded. Should be used to recover from a system crash.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT_FOUND(404), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415), CONFLICT(409)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "restart-mode=xstart" -X POST "http://localhost/ctrl"
```

**Notes :** Supported in bootserver mode

---

## Set Controller language

**Chemin :** Controller Service › Set Controller language

URL — /ctrl

**URL :** `/ctrl`  
**Method :** `POST`

**URL Params :**
```
action=set-lang
Required
See
Common URL parameters
```

**Data Params :**
```
lang
= {en|de} languages as per RFC 3066. if language is not supported, a bad request is sent as the http status.
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Set controller language
curl --digest -u "Default User":robotics -d "lang=de" -X POST "http://localhost/ctrl?action=set-lang"
```

**Notes :** Not Supported in bootserver mode

---

## Operations on Clock Resource

**Chemin :** Controller Service › Operations on Clock Resource

---

## Get Clock Resource

**Chemin :** Controller Service › Operations on Clock Resource › Get Clock Resource

URL — /ctrl/clock

**URL :** `/ctrl/clock`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-clock-info
datetime
The current system time in
YYYY-MM-DD T HH:MM:SS
format.
ctrl-timezone-li
Time zone resource, not supported on virtual controller
ctrl-timeserver-li
Time server resource, not supported on virtual controller
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/clock"
```

**Notes :** Not Supported in bootserver mode

---

## Get Clock Actions

**Chemin :** Controller Service › Operations on Clock Resource › Get Clock Actions

URL — /ctrl/clock

**URL :** `/ctrl/clock`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set-system-clock
sys-clock-year
=[Integer]
Required
, Minimum value
1900
sys-clock-month
=[Integer]
Required
, - Minimum
1
and Maximum
12
sys-clock-day
=[Integer]
Required
, - Minimum
1
and Maximum
31
sys-clock-hour
=[Integer]
Required
, - Minimum
0
and Maximum
23
sys-clock-min
=[Integer]
Required
, - Minimum
0
and Maximum
59
sys-clock-sec
=[Integer]
Required
, - Minimum
0
and Maximum
59
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/clock?action=show"
```

**Notes :** Not Supported in bootserver mode

---

## Set the Clock of the controller

**Chemin :** Controller Service › Operations on Clock Resource › Set the Clock of the controller

URL — /ctrl/clock

**URL :** `/ctrl/clock`  
**Method :** `PUT`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
sys-clock-year
= The year part of datetime
Required
sys-clock-month
= The month part of datetime
Required
sys-clock-day
= The day part of datetime
Required
sys-clock-hour
= The hour part of datetime
Required
sys-clock-min
= The minutes part of datetime
Required
sys-clock-sec
= The seconds part of datetime
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNAUTHORIZED(401), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415), See
Robot controller return codes

**Sample Call :**
```bash
Set the controller Clock
curl --digest -u "Default User":robotics -d "sys-clock-year=2014&sys-clock-month=03&sys-clock-day=14&sys-clock-hour=08&sys-clock-min=30&sys-clock-sec=0" -X PUT "http://localhost/ctrl/clock"
```

**Notes :** Available only for RC
Not Supported in bootserver mode

---

## Operations on Timezone Resource

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timezone Resource

---

## Get timezone resource

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timezone Resource › Get timezone resource

URL — /ctrl/clock/timezone

**URL :** `/ctrl/clock/timezone`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-timezone
timezone
The timezone as defined by the tz database (or tzdata)
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/clock/timezone"
```

**Notes :** Available only for RC
Not supported in bootserver mode

---

## Get timezone actions

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timezone Resource › Get timezone actions

URL — /ctrl/clock/timezone?action=show

**URL :** `/ctrl/clock/timezone?action=show`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set-timezone
Set timezone, string as defined by the tz database
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/clock/timezone?action=show"
```

**Notes :** Available only for RC
Not supported in bootserver mode

---

## Set the time zone

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timezone Resource › Set the time zone

URL — /ctrl/clock/timezone

**URL :** `/ctrl/clock/timezone`  
**Method :** `POST`

**URL Params :**
```
set-timezone
See
Common URL parameters
```

**Data Params :**
```
timezone
= Time zone as defined by the tz database
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
Set the time zone
curl --digest -u "Default User":robotics -d "timezone=Europe/Stockholm" -X POST "http://localhost/ctrl/clock/timezone?action=set-timezone"
```

**Notes :** Available only for RC
Not supported in bootserver mode

---

## Operations on Timeserver Resource

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timeserver Resource

---

## Get time server resource

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timeserver Resource › Get time server resource

URL — /ctrl/clock/timeserver

**URL :** `/ctrl/clock/timeserver`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-timeserver
timeserver
Address of used time server
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/clock/timeserver"
```

**Notes :** Available only for RC
Not supported in bootserver mode

---

## Get time server actions

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timeserver Resource › Get time server actions

URL — /ctrl/clock/timeserver?action=show

**URL :** `/ctrl/clock/timeserver?action=show`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/clock/timeserver?action=show"
```

**Notes :** Available only for RC
Not supported in bootserver mode

---

## Set the time server

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timeserver Resource › Set the time server

URL — /ctrl/clock/timeserver

**URL :** `/ctrl/clock/timeserver`  
**Method :** `POST`

**URL Params :**
```
action=set-timeserver
See
Common URL parameters
```

**Data Params :**
```
timeserver
= Time server
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
Set the time zone
curl --digest -u "Default User":robotics -d "timeserver=132.163.4.101" -X POST "http://localhost/ctrl/clock/timeserver?action=set-timeserver"
```

**Notes :** Available only for RC
Not supported in bootserver mode

---

## Test Time Server

**Chemin :** Controller Service › Operations on Clock Resource › Operations on Timeserver Resource › Test Time Server

URL — /ctrl/clock/timeserver

**URL :** `/ctrl/clock/timeserver`  
**Method :** `GET`

**URL Params :**
```
resource=servertime
Required
server-ip = {server ip}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-servertimer
gets the server time
time
UNIX time
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/clock/timeserver?resource=servertime&server-ip=129.6.15.28"
```

**Notes :** Available only for RC
Not supported in bootserver mode

---

## Operations on Identity Resource

**Chemin :** Controller Service › Operations on Identity Resource

---

## Get Identity Resource

**Chemin :** Controller Service › Operations on Identity Resource › Get Identity Resource

URL — /ctrl/identity

**URL :** `/ctrl/identity`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-identity-info
ctrl-name
Alphanumeric, the name of the controller.
ctrl-id
Alphanumeric, the controller id, available only for RC.
ctrl-type
Gives information whether controller is virtual controller or Real Controller.
ctrl-mac
Gives the controller MAC address, available only for RC.
ctrl-level
Gives information whether system is in bootserver mode or not.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/identity"
```

**Notes :** Supported in bootserver mode

---

## Get Identity Actions

**Chemin :** Controller Service › Operations on Identity Resource › Get Identity Actions

URL — /ctrl/identity

**URL :** `/ctrl/identity`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set-ctrl-identity
ctrl-name
=[alphanumeric]
Required
, the controller name
ctrl-id
=[alphanumeric]
Required
, the controller id
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/identity?action=show"
```

**Notes :** Supported in bootserver mode

---

## Set the Identity of the controller

**Chemin :** Controller Service › Operations on Identity Resource › Set the Identity of the controller

URL — /ctrl/identity

**URL :** `/ctrl/identity`  
**Method :** `PUT`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
ctrl-name
= The name of the controller
ctrl-id
= The controller ID
Atleast one data param should be present.
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** UNAUTHORIZED(401), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
See
Robot controller return codes

**Sample Call :**
```bash
Set the controller identity
curl --digest -u "Default User":robotics -d "ctrl-name=testcontroller&ctrl-id=ZZZZ" -X PUT "http://localhost/ctrl/identity"
```

**Notes :** Supported in bootserver mode

---

## Operations on System Resource

**Chemin :** Controller Service › Operations on System Resource

---

## Get list of installed systems

**Chemin :** Controller Service › Operations on System Resource › Get list of installed systems

URL — /ctrl/system

**URL :** `/ctrl/system`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-system-li
Ctrl-system resource
RW6_TEST
installed system
RW6_NEW
installed system
RW6_safey
installed system
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/system"
```

**Notes :** Supported in bootserver mode

---

## Get actions on system

**Chemin :** Controller Service › Operations on System Resource › Get actions on system

URL — /ctrl/system

**URL :** `/ctrl/system`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set-bootdevice
To set device path
load-bootimage
Load the boot Image
undo-load-bootinage
Undo the load boot image
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/system?action=show"
```

**Notes :** Supported in bootserver mode

---

## Set Boot Device

**Chemin :** Controller Service › Operations on System Resource › Set Boot Device

Description — Sets the device/path that should be used to load boot image

**URL :** `/ctrl/system`  
**Method :** `POST`

**URL Params :**
```
action=set-bootdevice
Required
See
Common URL parameters
```

**Data Params :**
```
path
Fully qualified path to be used for booting.
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u ""Default User":robotics -d "path={Path}" -X POST "
http://localhost/ctrl/system?action=set-bootdevice
"
```

**Notes :** Supported in bootserver mode only

---

## Get Boot Device

**Chemin :** Controller Service › Operations on System Resource › Get Boot Device

Description — Retrieves the device/path that should be used to load boot image

**URL :** `/ctrl/system`  
**Method :** `GET`

**URL Params :**
```
resource=boot-device
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/system?resource=boot-device"
```

**Notes :** Supported in bootserver mode only

---

## Load Boot Image

**Chemin :** Controller Service › Operations on System Resource › Load Boot Image

Description — Load the boot image from the predefined path

**URL :** `/ctrl/system`  
**Method :** `POST`

**URL Params :**
```
action=set-bootimage
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** Accepted (202), see
HTTP Status codes
Location header: /ctrl?action=show

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u ""Default User":robotics -d -X POST "
http://localhost/ctrl/system?action=set-bootimage
"
```

**Notes :** Supported in bootserver mode only
Controller must be restarted to reflect the changes
Not supported by VC

---

## Unload Boot Image

**Chemin :** Controller Service › Operations on System Resource › Unload Boot Image

Description — Undo the load boot image

**URL :** `/ctrl/system`  
**Method :** `POST`

**URL Params :**
```
action=undo-bootimage
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u ""Default User":robotics -d -X POST "
http://localhost/ctrl/system?action=undo-bootimage
"
```

**Notes :** Supported in bootserver mode only
Not supported by VC

---

## Get selected system name

**Chemin :** Controller Service › Operations on System Resource › Get selected system name

Description — Get the controller active system name.

**URL :** `/ctrl/system`  
**Method :** `GET`

**URL Params :**
```
type=selected
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/system?type=selected"
```

**Notes :** Not supported in VC
Supported in Bootserver In bootserver, system-name will show as BOOTSERVER, as active system is not applicable in bootserver mode

---

## Install deployment package

**Chemin :** Controller Service › Operations on System Resource › Install deployment package

URL — /ctrl/system/installdpkg

**URL :** `/ctrl/system/installdpkg`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
ctrl-id
=<ctrl-id>
ctrl-name
=<ctrl-name>
system-path
=<system-path>
Required
dp-pkg-path
=<dp-pkg-path>
Required
```

**Success :** ACCEPTED(202)
Location header: dpkginstallationstatus
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u ""Default User":robotics -d "ctrl-id=1231&ctrl-name=Ctrlname&system-path=Systems/DeploymentTest&dp-pkg-path=/hd0a/inbox" -X POST "
http://localhost/ctrl/system/installdpkg
"
```

**Notes :** Supported in bootserver mode only. Will validate the deployment package internally. To get status of the installation, see location header. System will be restarted after unpacking the files. dp-pkg-path should be inside inbox folder.The installation package and all associated files should be placed in the /hd0a/inbox directory, and it is recommended to use Robot Studio for copying the package.

---

## Validate deployment package

**Chemin :** Controller Service › Operations on System Resource › Validate deployment package

URL — /ctrl/system/validatedpkg

**URL :** `/ctrl/system/validatedpkg`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
path
={path}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u ""Default User":robotics -d "path=/hd0a/inbox/TEMP" -X POST "
http://localhost/ctrl/system/validatedpkg
"
```

**Notes :** Supported in bootserver mode only. path should be inside inbox folder.

---

## Get system resource

**Chemin :** Controller Service › Operations on System Resource › Get system resource

URL — /ctrl/system/{system-name}

**URL :** `/ctrl/system/{system-name}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/system/RW6_02_048"
```

**Notes :** Supported in bootserver mode

---

## Get actions on a system resource

**Chemin :** Controller Service › Operations on System Resource › Get actions on a system resource

URL — /ctrl/system/{system-name}

**URL :** `/ctrl/system/{system-name}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
rename
Rename a system
newname
- The system's new name
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/system/RW6_02_048?action=show"
```

**Notes :** Supported in bootserver mode

---

## Rename a system

**Chemin :** Controller Service › Operations on System Resource › Rename a system

URL — /ctrl/system/{system-name}

**URL :** `/ctrl/system/{system-name}`  
**Method :** `POST`

**URL Params :**
```
action=rename
Required
See
Common URL parameters
```

**Data Params :**
```
newname={new system name}
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "newname=System123" -X POST "http://localhost/ctrl/system/RW6_TEST?action=rename"
```

**Notes :** Only available for VxWorks in "System-Mode". Not available for VC or Boot-Server.

---

## Select a system

**Chemin :** Controller Service › Operations on System Resource › Select a system

Description — Select a system to activate. A restart is required after selecting to activate the system.

**URL :** `/ctrl/system/{system-name}`  
**Method :** `POST`

**URL Params :**
```
action=activate
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** UNAUTHORIZED(401), BAD_REQUEST(400), CONFLICT(409)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/ctrl/system/RW6_TEST?action=activate"
```

**Notes :** status code CONFLICT is returned if trying to select a system that is already active.

---

## Delete a System

**Chemin :** Controller Service › Operations on System Resource › Delete a System

URL — /ctrl/system/{system-name}

**URL :** `/ctrl/system/{system-name}`  
**Method :** `DELETE`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
Delete a System
curl --digest -u "Default User":robotics -X DELETE "http://localhost/ctrl/system/RW6_TEST"
```

**Notes :** Supported in bootserver mode
not supported in VC

---

## Deselect a System

**Chemin :** Controller Service › Operations on System Resource › Deselect a System

Description — De-activate an active system. A restart is required after de-activating the system.

**URL :** `/ctrl/system`  
**Method :** `POST`

**URL Params :**
```
action=deactivate
Required
See
Common URL parameters
```

**Data Params :**
```
none
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/ctrl/system?action=deactivate"
```

**Notes :** Not supported in Virtual Controller

---

## Operations on network Resource

**Chemin :** Controller Service › Operations on network Resource

---

## Get Network Resource

**Chemin :** Controller Service › Operations on network Resource › Get Network Resource

URL — /ctrl/network

**URL :** `/ctrl/network`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-netw
addr
IP addresses of the network interface.
mask
Mask of the network interface.
name
Name of the network interface.
dhcp
{Enabled | Disabled} DHCP status of the network interface (if applicable).
gateway
Default gateway of the network interface (if applicable).
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/network"
```

**Notes :** Supported in bootserver mode

---

## Get Network setting actions

**Chemin :** Controller Service › Operations on network Resource › Get Network setting actions

Description — Get possible actions with forms on network setting

**URL :** `/ctrl/network`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set
To set IP configuration for the LAN adaptor
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/network?action=show"
```

**Notes :** Supported in bootserver mode.
Not supported by VC.

---

## Set Network configuration

**Chemin :** Controller Service › Operations on network Resource › Set Network configuration

URL — /ctrl/network

**URL :** `/ctrl/network`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
See
Common URL parameters
```

**Data Params :**
```
method
= {IP config method}, Should be one of
fixip
or
dhcp
or
noip
Required
address
= {IP address}, Applicable only for setting fix IP
mask
= {Mask address}, Applicable only for setting fix IP
gateway
={Default Gateway}, Applicable only for setting fix IP
```

**Success :** Accepted (202)
Location header: /ctrl?action=show
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=fixip&address={IP address}&mask={Mask address}&gateway={Default Gateway}" -X POST "http://localhost/ctrl/network?action=set"
```

**Notes :** Supported in bootserver mode.
Not supported by VC.
Controller must be restarted to reflect the changes.
Requires the UAS grant UAS_CONTROLLER_PROPERTIES_WRITE

---

## Operations on DNS Resource

**Chemin :** Controller Service › Operations on network Resource › Operations on DNS Resource

---

## Get DNS Resource

**Chemin :** Controller Service › Operations on network Resource › Operations on DNS Resource › Get DNS Resource

URL — /ctrl/network/dns

**URL :** `/ctrl/network/dns`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-netw
name
DNS name.
addr
IP address of name server.
port
DNS port number.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/network/dns"
```

**Notes :** Supported in bootserver mode
Not supported by VC.

---

## Operations on Routing Table Resource

**Chemin :** Controller Service › Operations on network Resource › Operations on Routing Table Resource

---

## Add a route table entry

**Chemin :** Controller Service › Operations on network Resource › Operations on Routing Table Resource › Add a route table entry

URL — /ctrl/network/route/add

**URL :** `/ctrl/network/route/add`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
destination
={destination}, Destination is either a host address or a destination network.
Required
gateway
= {gateway}, Gateway is the address used to reach the destination.
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "destination=192.168.136.0/24&gateway=192.168.126.200" -X POST "http://localhost/ctrl/network/route/add"
curl --digest -u "Default User":robotics -d "destination=10.10.10.3&gateway=192.168.125.254" -X POST "http://localhost/ctrl/network/route/add"
```

**Notes :** Supported in bootserver mode.
Not supported by VC.

---

## Options to add a route table entry

**Chemin :** Controller Service › Operations on network Resource › Operations on Routing Table Resource › Options to add a route table entry

URL — /ctrl/network/route/add

**URL :** `/ctrl/network/route/add`  
**Method :** `OPTIONS`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Actions :**
```
addroute
destination
The host address or the destination network.
gateway
Address used to reach the destination.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X OPTIONS "http://localhost/ctrl/network/route/add"
```

**Notes :** Supported in bootserver mode.
Not supported by VC.

---

## Remove a route table entry

**Chemin :** Controller Service › Operations on network Resource › Operations on Routing Table Resource › Remove a route table entry

URL — /ctrl/network/route/remove

**URL :** `/ctrl/network/route/remove`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
destination
={destination}, Destination is either a host address or a destination network.
Required
```

**Success :** Accepted(202)
Location header: /ctrl?action=show
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "destination=192.168.136.0/24" -X POST "http://localhost/ctrl/network/route/remove"
```

**Notes :** The routing entry will be removed from the network stack routing table after reboot.
Supported in bootserver mode.
Not supported by VC.

---

## Options to remove a route table entry

**Chemin :** Controller Service › Operations on network Resource › Operations on Routing Table Resource › Options to remove a route table entry

URL — /ctrl/network/route/remove

**URL :** `/ctrl/network/route/remove`  
**Method :** `OPTIONS`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Actions :**
```
removeroute
destination
The host address or the destination network.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X OPTIONS "http://localhost/ctrl/network/route/remove"
```

**Notes :** Supported in bootserver mode.
Not supported by VC.

---

## Operations on Backup Resource

**Chemin :** Controller Service › Operations on Backup Resource

---

## Get backup resources

**Chemin :** Controller Service › Operations on Backup Resource › Get backup resources

URL — /ctrl/backup

**URL :** `/ctrl/backup`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/backup"
```

**Notes :** Not supported in bootserver mode

---

## Get backup actions

**Chemin :** Controller Service › Operations on Backup Resource › Get backup actions

Description — Get available actions on backup

**URL :** `/ctrl/backup`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Actions :**
```
backup
The file path to store the backup e.g. backup=/fileservice/$syspar/tempfolder
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/backup?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Create a Backup

**Chemin :** Controller Service › Operations on Backup Resource › Create a Backup

URL — /ctrl/backup

**URL :** `/ctrl/backup`  
**Method :** `POST`

**URL Params :**
```
action=backup
Required
See
Common URL parameters
```

**Data Params :**
```
backup
= path where the backup shall be stored. Destination path must be part of the controller file system.
Required
Environment variables such as $TEMP, $SYSTEM shall be possible to have in the path. But $HOME directory cannot be used as backup path. Example: backup=/fileservice/$syspar/tempfolder
archive=TRUE | FALSE
```

**Success :** ACCEPTED(202)
Location header: /progress/{id}
see
HTTP Status codes

**Error :** UNAUTHORIZED(401), FORBIDDEN(403), BAD_REQUEST(400), CONFLICT(409)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "backup=/fileservice/$syspar/tempfolder" -X POST "http://localhost/ctrl/backup?action=backup"
```

**Notes :** Requires UAS grant UAS_BACKUP.
It is not possible to create backup with the same path and name as an environment variable directory (SYSTEM, HOME, SYSPAR etc).
It is not possible create backup under HOME directory.
Since backup is an asynchronous task, the location header can be subscribed on to get information about the status of the task.
Not supported in bootserver mode

---

## Restore a backup.

**Chemin :** Controller Service › Operations on Backup Resource › Restore a backup.

URL — /ctrl/backup

**URL :** `/ctrl/backup`  
**Method :** `POST`

**URL Params :**
```
action=restore
Required
See
Common URL parameters
```

**Data Params :**
```
backup
= {path where the backup is stored}
Required
. Path must be part of the controller file system. Environment variables such as $TEMP, $SYSTEM shall be possible to have in the path. Example: backup=/fileservice/$syspar/tempfolder
ignore
= {all | system-id | template-id | none} Mismatches between backup and current system that should be ignored at restore. Defaults to none
delete-dir
= {true | false} Indicate whether the backup directory should be deleted after the restore is finished. Defaults to true
include-cs
={true |false } Indicate if controller settings are to be included in the restore. Defaults to true
include-ss
={true |false } Indicate if safety settings are to be included in the restore. Defaults to true
include
={ cfg| modules | all } Indicate if what is to be included in the restore. Defaults to all
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), FORBIDDEN(403), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
`curl –digest -u "Default User":robotics -d "backup=/fileservice/$syspar/tempfolder" -X POST "http://localhost/ctrl/backup?action=restore"
```

**Notes :** Requires UAS grant Restore a backup
Not supported in bootserver mode

---

## Check Restore

**Chemin :** Controller Service › Operations on Backup Resource › Check Restore

URL — /ctrl/backup

**URL :** `/ctrl/backup`  
**Method :** `GET`

**URL Params :**
```
action
=check-restore
Required
backup
={path where the backup is stored}
REQUIRED
. Path must be part of the controller file system. Environment variables such as $TEMP, $SYSTEM shall be possible to have in the path. Example: backup=/fileservice/$syspar/tempfolder
ignore
={all | system-id | template-id | none} Mismatches between backup and current system that should be ignored at restore.
include-cs
={true |false } Indicate if controller settings are to be included in the restore
includess
={true |false } Indicate if safety settings are to be included in the restore
include
={ cfg| modules | all } Indicate if what is to be included in the restore.
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
status
- {Accepted}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/backup?action=check-restore&backup=/fileservice/$syspar/tempfolder"
```

**Notes :** Not supported in bootserver mode

---

## Get Backup State

**Chemin :** Controller Service › Operations on Backup Resource › Get Backup State

Description — Get status of backup

**URL :** `/ctrl/backup`  
**Method :** `GET`

**URL Params :**
```
action=backupstate
Required
See
Common URL parameters
```

**Resources :**
```
backup state
- {None | Init State | Backup in Progress | Backup Ready | Error during backup | Invalid}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/backup?action=backupstate"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on Backup System Information

**Chemin :** Controller Service › Operations on Backup Resource › Subscribe on Backup System Information

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/progress/{id} ')
Required
<identifier>-p = The priority associated with the subscription resource.
Required
```

**Success :** CREATED(201), see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/progress/1;state&1-p=0" -X POST "http://localhost/subscription"
```

**Notes :** if the subscription is created during backup creation of the System (backup.log is in progress),the state will be in "pending".
Not supported in bootserver mode.
Not supported on virtual controller.

---

## Operations on backup system information

**Chemin :** Controller Service › Operations on Backup Resource › Operations on backup system information

---

## Get backup system information

**Chemin :** Controller Service › Operations on Backup Resource › Operations on backup system information › Get backup system information

URL — /ctrl/backup/info/

**URL :** `/ctrl/backup/info/`  
**Method :** `GET`

**URL Params :**
```
backup-path={path to a backup system folder}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/backup/info?backup-path=C:/Users/inshsal/Documents/RobotStudio/Systems/BACKUP/mybackup"
```

**Notes :** Not Supported in bootserver mode

---

## Operations on Compress Resource

**Chemin :** Controller Service › Operations on Compress Resource

---

## Get compress resources

**Chemin :** Controller Service › Operations on Compress Resource › Get compress resources

URL — /ctrl/compress

**URL :** `/ctrl/compress`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/compress"
```

**Notes :** Not supported in bootserver mode

---

## Get compress actions

**Chemin :** Controller Service › Operations on Compress Resource › Get compress actions

URL — /ctrl/compress

**URL :** `/ctrl/compress`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
comp
Compress
srcpath
The source resource to compress
dstpath
The destination path where the compressed file shall be stored.
dcomp
De-Compress
srcpath
The source resource to decompress
dstpath
The destination path where the decompressed files shall be stored.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/compress?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Compress/Decompress Resource

**Chemin :** Controller Service › Operations on Compress Resource › Compress/Decompress Resource

Description — Enables the user to compress and decompress resources i.e. files or directories.

**URL :** `/ctrl/compress`  
**Method :** `POST`

**URL Params :**
```
action={comp|dcomp}
Required
action=comp
for compress and
action=dcomp
for decompress
See
Common URL parameters
```

**Data Params :**
```
srcpath
={compress/decompress path} File or directory to compress/decompress
Required
dstpath
={destination path} path where the compressed/decompressed file shall be stored.
Required
Environment variables such as $TEMP, $SYSTEM shall be possible to have in the path.
```

**Success :** ACCEPTED(202)
Location header: /progress/{id}
see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "srcpath=/fileservice/$system/Folder1&dstpath=/fileservice/$syspar/" -X POST "http://localhost/ctrl/compress?action=comp"
curl --digest -u "Default User":robotics -d "srcpath=/fileservice/$syspar/Folder1.rzo&dstpath=/fileservice/$syspar/" -X POST "http://localhost/ctrl/compress?action=dcomp"
```

**Notes :** Compression of HOME folder, its sub directories, and SYSTEM folder is not allowed.
While decompressing a compressed file or a folder to a destination path, if a file or a folder with the same name as the compressed file name is already existing, it will be overwritten by the contents of the decompressed file or folder.
Since compression and decompression of resources are asynchronous tasks, the location header can be subscribed on to get information about the status of the tasks.
Not supported in bootserver mode.

---

## Operations on Diagnostics Resource

**Chemin :** Controller Service › Operations on Diagnostics Resource

---

## Get diagnostics resources

**Chemin :** Controller Service › Operations on Diagnostics Resource › Get diagnostics resources

URL — /ctrl/diagnostics

**URL :** `/ctrl/diagnostics`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/diagnostics"
```

**Notes :** Not supported in bootserver mode.
Not supported on Virtual Controller.

---

## Get diagnostics actions

**Chemin :** Controller Service › Operations on Diagnostics Resource › Get diagnostics actions

URL — /ctrl/diagnostics

**URL :** `/ctrl/diagnostics`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
save
Save the system diagnostics
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/diagnostics?action=show"
```

**Notes :** Not supported in bootserver mode.
Not supported on Virtual Controller.

---

## Save system diagnostics

**Chemin :** Controller Service › Operations on Diagnostics Resource › Save system diagnostics

URL — /ctrl/diagnostics

**URL :** `/ctrl/diagnostics`  
**Method :** `POST`

**URL Params :**
```
action=save
Required
See
Common URL parameters
```

**Data Params :**
```
dstpath
=Fully qualified file name to save the diagnostic log e.g.fileservice/hd0a/TEMP/sysdump/diagnostics.log. The path can contain environment variables.
Required
```

**Success :** ACCEPTED(202), see
HTTP Status codes
Location header: /progress/{id}

**Error :** BAD_REQUEST(400), CONFLICT(409), UNSUPPORTED_MEDIA(415) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "dstpath=/fileservice/$TEMP/sysdump/diagnostics.log" -X POST "http://localhost/ctrl/diagnostics?action=save"
```

**Notes :** Since saving a diagnostic log is an asynchronous task, the location header can be subscribed on to get information about the status of the task.
Not supported in bootserver mode.
Not supported on Virtual Controller.

---

## Subscribe on system dump

**Chemin :** Controller Service › Operations on Diagnostics Resource › Subscribe on system dump

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/ctrl/diagnostics')
Required
<identifier>-p = The priority associated with the subscription resource.
Required
```

**Resources :**
```
sysdump:
to obtain the system dump.
```

**Success :** CREATED(201), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/ctrl/diagnostics&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/ctrl/diagnostics&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** If there is no system dump available in the controller, the initial response will be empty.
Also, if the subscription is created when a system dump is in progress, the initial response will be empty.
if an client has already subscribed on the system dump resource(/ctrl/diagnostics), and the existing system dump folder has been deleted or moved, Path sent in the initial response can be invalid for the new client's subscribing on this resource since the folder has been deleted after the dump was created.
Not supported in bootserver mode.
Not supported on virtual controller.

---

## Subscribe on Diagnostics States (Get System Diagnostics)

**Chemin :** Controller Service › Operations on Diagnostics Resource › Subscribe on Diagnostics States (Get System Diagnostics)

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/progress/{id} ')
Required
<identifier>-p = The priority associated with the subscription resource.
Required
```

**Success :** CREATED(201), see
HTTP Status codes

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/progress/1;state&1-p=0" -X POST "http://localhost/subscription"
```

**Notes :** if the subscription is created when save System Diagnostics(diagnostics.log is in progress),the state will be in "pending".
Not supported in bootserver mode.
Not supported on virtual controller.

---

## Operations on CtrlSafetyResource

**Chemin :** Controller Service › Operations on CtrlSafetyResource

---

## Get safety resources

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get safety resources

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety"
```

**Notes :** Supported in bootserver mode

---

## Get Safety actions

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get Safety actions

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
action=show
Required
Returns action forms for this resource
```

**Data Params :**
```
None
```

**Actions :**
```
load
- Load a Safety configuration file.
filepath
=[file path]
Required
, RobotWare environ variables such as $HOME, $TEMP can be used in the filepath.
action-type
=[load]
Required
.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Retrieve actions on the CFG resource
curl --digest -u "Default User":robotics" "
http://localhost/ctrl/safety?action=show
"
Load Safety CFG file
curl --digest -u "Default User":robotics -d "filepath=$TEMP/safety.xml" -X POST
http://localhost/ctrl/safety?action=show
```

**Notes :** Not supported in bootserver mode

---

## Load Safety configuration file to controller

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Load Safety configuration file to controller

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `POST`

**URL Params :**
```
action=load
Required
See
Common URL parameters
```

**Data Params :**
```
filepath
=Safety configuration file path on controller
Required
```

**Success :** HTTP_OK(200)

**Error :** BAD_REQUEST(400), NOT_FOUND(404), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
Rename a file
curl --digest -u "Default User":robotics -d "filepath=$home/file.xml" -X POST "http://localhost/ctrl/safety?action=load"
```

**Notes :** Not supported in bootserver mode

---

## Set Safety Mode of the controller

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Set Safety Mode of the controller

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `POST`

**URL Params :**
```
action=set-mode
Required
See
Common URL parameters
```

**Data Params :**
```
mode= { active | commissioning | service }
Required
```

**Success :** NO_CONTENT(204)
See
Robot controller return codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mode=service" -X POST "http://localhost/ctrl/safety?action=set-mode"
```

**Notes :** Not supported in bootserver mode
Controller shoul be in manual mode

---

## Get Config status

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get Config status

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
resource=config-status
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
ScorchConfigStatus
- config status.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety?resource=config-status"
```

**Notes :** Not supported in bootserver mode

---

## Get Safety Mode status

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get Safety Mode status

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
resource=safety-mode
Required
```

**Data Params :**
```
None
```

**Resources :**
```
userdata
- User Data.
safetymode
- safety Mode {SCORCH_SAFETY_MODE_ACTIVE_MODE|SCORCH_SAFETY_MODE_COMMISSIONING_MODE|SCORCH_SAFETY_MODE_SERVICE_MODE}
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety?resource=safety-mode"
```

**Notes :** Not supported in bootserver mode

---

## Get Safety Cyclic Brake Check status

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get Safety Cyclic Brake Check status

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
resource=cbc-status
Required
drivenum={mech unit drive number}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
time-interval
- time interval for device brake check
cbc-test-status
- execution of brake check test status { CBC_TEST_OK(ok)|CBC_TEST_WARNING(warning)|CBC_TEST_ERROR(error)|CBC_TEST_UNDEFINED(undefined)}
cbc-status
- Cyclic Brake Check status {CBC_STATUS_OK(ok)|CBC_STATUS_PREWARNING(warning)|CBC_STATUS_REQUIRE_CBC(required)}
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety?resource=cbc-status&drivenum=1"
```

**Notes :** Not supported in bootserver mode

---

## Get LoadOperation status

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get LoadOperation status

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
resource=loadoperation-status
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
scorchloadoperationstatus
- LoadOperation status {OK|SCORCH_ERR_OPTION_NOT_PRESENT|SCORCH_ERR_NOT_IN_MANUAL_MODE|SCORCH_ERR_NOT_IN_MOTORS_OFF|SCORCH_ERR_CURRENT_CONFIG_LOCKED|SCORCH_ERR_USER_GRANT_IS_MISSING}.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety?resource=loadoperation-status"
```

**Notes :** Not supported in bootserver mode
User should have Safety services privileges

---

## Get Safety Configurations

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get Safety Configurations

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
resource=safety-config
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
safety-ctrl-configuration
Ctrl-Safety resource
sw-major-ver
software major version
sw-minor-ver
software minor version
sw-rev
software revision
file-major-ver
file major version
file-minor-ver
file minor version
file-rev
file revision
creation-date
String on format YYYY-MM-DDThh:mm:ss.fffffff+zz:zz
created-by
Created By
config-name
configuration name
checksum
checksum as base64 encoded data
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety?resource=safety-config"
```

**Notes :** Not supported in bootserver mode

---

## Get Safety Violation Info

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Get Safety Violation Info

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `GET`

**URL Params :**
```
resource=violation-info
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
safety-violationinfo
violation-type
none
stz
- Safe Tool Zone
sar
- Safe Axis Range
sts
- Safe Tool Speed
sas
- Safe Axis Speed
tom
- Tool Orientation Monitoring
osr
- Operational Safety Range (Area?)
sst
- Safe Standstill
red_tool_speed
- Reduced Tool Speed (Manual mode)
red_axis_speed
- Reduced Axis Speed (Manual mode)
unsync_speed_lim
- Reduced Axis Speed due to unsynchronized robot
empstop
- EmStop triggered
other
- Internal error
invalid
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety?resource=violation-info"
```

**Notes :** Not supported in bootserver mode
User should have Safety services privileges

---

## Unlock the safety configuration

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Unlock the safety configuration

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `POST`

**URL Params :**
```
action=unlock
Required
See
Common URL parameters
```

**Data Params :**
```
none
```

**Success :** NO_CONTENT(204)

**Error :** BAD_REQUEST(400), NOT_FOUND(404), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
Rename a file
curl --digest -u "Default User":robotics -d "index=0" -X POST "http://localhost/ctrl/safety?action=syncack"
```

**Notes :** Not supported in bootserver mode

---

## Software Sync Acknowledgement

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Software Sync Acknowledgement

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `POST`

**URL Params :**
```
action=syncack
Required
See
Common URL parameters
```

**Data Params :**
```
index={0 | 1}
mandatory
```

**Success :** NO_CONTENT(204)

**Error :** BAD_REQUEST(400), NOT_FOUND(404), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
Rename a file
curl --digest -u "Default User":robotics -d "index=0" -X POST "http://localhost/ctrl/safety?action=syncack"
```

**Notes :** Not supported in bootserver mode

---

## Add Validation info

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Add Validation info

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `POST`

**URL Params :**
```
action=validate-cfg
Required
See
Common URL parameters
```

**Data Params :**
```
validated-by={name}
Required
```

**Success :** NO_CONTENT(204)
See
Robot controller return codes

**Error :** BAD_REQUEST(400),FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
`curl –digest -u "Default User":robotics -d "validated-by=abc" -X POST "http://localhost/ctrl/safety?action=validate-cfg"
```

**Notes :** Must have grant UAS_SAFETY_SERVICES for method to succeed
Not supported in bootserver mode

---

## Remove Validation info

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Remove Validation info

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `POST`

**URL Params :**
```
action=invalidate-cfg
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
See
Robot controller return codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
`curl –digest -u "Default User":robotics POST "http://localhost/ctrl/safety?action=invalidate-cfg"
```

**Notes :** Must have grant UAS_SAFETY_SERVICES for method to succeed
Not supported in bootserver mode

---

## Set Reset Safety Controller

**Chemin :** Controller Service › Operations on CtrlSafetyResource › Set Reset Safety Controller

URL — /ctrl/safety

**URL :** `/ctrl/safety`  
**Method :** `POST`

**URL Params :**
```
action=reset
Required
See
Common URL parameters
```

**Success :** NO_CONTENT(204), See
Robot controller return codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/safety?action=reset"
```

**Notes :** Not supported in bootserver mode
User should have Safety services privileges

---

## Operations on options Resource

**Chemin :** Controller Service › Operations on options Resource

---

## Get options resource

**Chemin :** Controller Service › Operations on options Resource › Get options resource

URL — /ctrl/options/{option to verify}

**URL :** `/ctrl/options/{option to verify}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), for /ctrl/options/{option to verify}
NO_CONTENT(204), /ctrl/options
see
HTTP Status codes

**Error :** NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/options/SAFEMOVEPRO"
```

**Notes :** The option to be verified is to provided as part of the request url. Also, the url is case sensitive. see example above. Not Supported in bootserver mode

---

## Operations on Compatabile Resource

**Chemin :** Controller Service › Operations on Compatabile Resource

---

## Check Robotware version compatibility with contorller hardware

**Chemin :** Controller Service › Operations on Compatabile Resource › Check Robotware version compatibility with contorller hardware

URL — /ctrl/compatibility/{robotware version}

**URL :** `/ctrl/compatibility/{robotware version}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT FOUND(404), BAD REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/compatibility/6.03.0101"
```

**Notes :** Supported only in RC.
Supported in bootserver mode.

---

## Operation on Virtual Time

**Chemin :** Controller Service › Operation on Virtual Time

---

## Get Virtual Time resources

**Chemin :** Controller Service › Operation on Virtual Time › Get Virtual Time resources

URL — /ctrl/virtualtime

**URL :** `/ctrl/virtualtime`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
vttimeslice
get the virtual timeslice value in milliseconds.
vttime
get the virtual time value in milliseconds.
vtspeed
get the speed of virtual time in percent relative to real time.
vtstate
get the state of the virtual time server {VTSTOP | VTFREERUN | VTRUNSLICE | VTNEXTEVENT}
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime"
```

**Notes :** Not supported in bootserver mode
Supported only in VC.

---

## Operation on VTTime

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTTime

---

## Get Virtualtime

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTTime › Get Virtualtime

URL — /ctrl/virtualtime/vttime

**URL :** `/ctrl/virtualtime/vttime`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-vttime
controller virtualtime resource
vtcounter
virtual time in milliseconds.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** Not Found(404)
see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime/vttime"
```

**Notes :** Supported only in VC mode

---

## Operation on VTTimeslice

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTTimeslice

---

## Get VTTimeslice Value

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTTimeslice › Get VTTimeslice Value

URL — /ctrl/virtualtime/vttimeslice

**URL :** `/ctrl/virtualtime/vttimeslice`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT FOUND(404),
BAD REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime/vttimeslice"
```

**Notes :** Supported only in VC.
vttimeslice value is in ms.
Not supported in bootserver mode.

---

## Actions on VTTimeslice

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTTimeslice › Actions on VTTimeslice

URL — /ctrl/virtualtime/vttimeslice

**URL :** `/ctrl/virtualtime/vttimeslice`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime/vttimeslice"
```

**Notes :** Supported only in VC.
vttimeslice value is in ms.
Not supported in bootserver mode.

---

## Set VTTimeslice Value

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTTimeslice › Set VTTimeslice Value

URL — /ctrl/virtualtime/vttimeslice

**URL :** `/ctrl/virtualtime/vttimeslice`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
vttimeslice={value} in ms
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** NOT FOUND(404)
BAD REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "vttimeslice=20" -X POST "http://localhost/ctrl/virtualtime/vttimeslice"
```

**Notes :** Supported only in VC.
Value should be in ms.
For values < 10 ms. vttimeslice will be set to a default value of 10 ms.
Not supported in bootserver mode.

---

## Operation on VTSpeed

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTSpeed

---

## Get Speed of Virtual Time

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTSpeed › Get Speed of Virtual Time

URL — /ctrl/virtualtime/vtspeed

**URL :** `/ctrl/virtualtime/vtspeed`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-vtspeed
controller virtualtime resource
vtcurrspeed
speed of virtual time in percent relative to real time.-1 equals full speed, 0 equals 100 percent.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime/vtspeed"
```

**Notes :** Not supported in bootserver mode
Supported only in VC.

---

## Get actions on a VTSpeed

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTSpeed › Get actions on a VTSpeed

URL — /ctrl/virtualtime/vtspeed

**URL :** `/ctrl/virtualtime/vtspeed`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
vtspeed
Sets the speed of virtual time in percent relative to real time
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime/vtspeed?action=show"
```

**Notes :** Not supported in bootserver mode
Supported only in VC.

---

## Set Speed of Virtualtime

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTSpeed › Set Speed of Virtualtime

URL — /ctrl/virtualtime/vtspeed

**URL :** `/ctrl/virtualtime/vtspeed`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
vtspeed={value}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400)
UNSUPPORTED_MEDIA(415)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "vtspeed=100" -X POST "http://localhost/ctrl/virtualtime/vtspeed"
```

**Notes :** Supported only in VC.
Not supported in bootserver mode.

---

## Operation on VTState

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTState

---

## Get State of Virtual Time

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTState › Get State of Virtual Time

URL — /ctrl/virtualtime/vtstate

**URL :** `/ctrl/virtualtime/vtstate`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrl-vtstate
controller virtualtime resource
vtcurrstate
gets the state of the virtual time server {VTSTOP | VTFREERUN | VTRUNSLICE | VTNEXTEVENT}
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime/vtstate"
```

**Notes :** Not supported in bootserver mode
Supported only in VC.

---

## Get actions on a VTState

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTState › Get actions on a VTState

URL — /ctrl/virtualtime/vtstate

**URL :** `/ctrl/virtualtime/vtstate`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
vtstate
sets the state of the virtual time server
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/ctrl/virtualtime/vtstate?action=show"
```

**Notes :** Not supported in bootserver mode
Supported only in VC.

---

## Set State of Virtualtime

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTState › Set State of Virtualtime

URL — /ctrl/virtualtime/vtstate

**URL :** `/ctrl/virtualtime/vtstate`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
vtstate={state_value}
Required
"state_value" will be {VTSTOP | VTFREERUN | VTRUNSLICE | VTNEXTEVENT}
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400)
UNSUPPORTED_MEDIA(415)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "vtstate=VTFREERUN" -X POST "http://localhost/ctrl/virtualtime/vtstate"
```

**Notes :** Supported only in VC.
Not supported in bootserver mode.

---

## Operation on VTRun

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTRun

---

## VT Run

**Chemin :** Controller Service › Operation on Virtual Time › Operation on VTRun › VT Run

URL — /ctrl/virtualtime/vtrun

**URL :** `/ctrl/virtualtime/vtrun`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/ctrl/virtualtime/vtrun"
```

**Notes :** Supported only in VC.
Not supported in bootserver mode.

---

## File Service

**Chemin :** File Service

---

## Get File Service Resources

**Chemin :** File Service › Get File Service Resources

URL — /fileservice

**URL :** `/fileservice`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
fs-device
fs-device-type
One of
fixed
,
removable
,
ramdisk
,
remote
or
unknown
.
fs-total-space
Total capacity of the media in bytes
fs-free-space
Available free space on the media in bytes.
fs-enabled
If the device is accessible, typically if you add a device before you set it as enabled
fs-readonly
TRUE if read only else FALSE
```

**Success :** HTTP_OK(200)

**Error :** UNAUTHORIZED(401),NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
Get a list of root resources
curl --digest -u "Default User":robotics "http://localhost/fileservice"
```

**Notes :** Though root supports environment variables these are not listed in the returned response.
Environment variables are only allowed directly under the root URI i.e. /fileservice/$home
Supported in bootserver mode

---

## Operations on Directory Resource

**Chemin :** File Service › Operations on Directory Resource

---

## Get Directory listing of resources

**Chemin :** File Service › Operations on Directory Resource › Get Directory listing of resources

URL — /fileservice/{environment_variable|device}/{directory}

**URL :** `/fileservice/{environment_variable|device}/{directory}`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
fs-dir
fs-cdate
The creation date of the resource in
YYYY-MM-DD T HH:MM:SS
format
fs-mdate
The time of last modification of the resource in
YYYY-MM-DD T HH:MM:SS
format
fs-file
fs-cdate
The creation date of the resource in
YYYY-MM-DD T HH:MM:SS
format
fs-mdate
The time of last modification of the resource in
YYYY-MM-DD T HH:MM:SS
format
fs-size
The size of file on the media in bytes.
fs-readonly
A boolean specifying if a file is read only or not. Possible values are: true and false
```

**Success :** HTTP_OK(200)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
Directory Listing
curl --digest -u "Default User":robotics "http://localhost/fileservice/$home"
```

**Notes :** Supported in bootserver mode

---

## Get Directory Actions

**Chemin :** File Service › Operations on Directory Resource › Get Directory Actions

URL — /fileservice/{device}|{directory}

**URL :** `/fileservice/{device}|{directory}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
fs-create
fs-newname
=[alphanumeric]
Required
fs-rename
fs-newname
=[alphanumeric]
Required
fs-copy
fs-newname
=[alphanumeric]
Required
fs-overwrite
=[true|false]
Required
, Multiple selection
fs-delete
Delete a directory
```

**Success :** HTTP_OK(200)

**Error :** BAD_REQUEST(400) See
Robot controller return codes

**Sample Call :**
```bash
Get actions on directory
curl --digest -u "Default User":robotics "http://localhost/fileservice/$home/docs?action=show"
```

**Notes :** Supported in bootserver mode

---

## Create a directory

**Chemin :** File Service › Operations on Directory Resource › Create a directory

URL — /fileservice/{device|environment_variable}/{directory}

**URL :** `/fileservice/{device|environment_variable}/{directory}`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
fs-newname
=The new directory name. See
Notes
below
Required
fs-action
=create
Required
```

**Success :** CREATED(201)

**Error :** UNAUTHORIZED(401), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415),
See
Robot controller return codes

**Sample Call :**
```bash
Create a new directory
curl --digest -u "Default User":robotics -d "fs-newname=newdir&fs-action=create" -X POST "http://localhost/fileservice/$home/"
```

**Notes :** Only relative path are allowed for "*fs-newname*". Absolute paths are not supported
The
fs-newname
can take nested directory structure e.g.
fs-newname=parentdir/subdir
will create both the directories if they don't exist i.e.
subdir
under
parentdir
Supported in bootserver mode

---

## Rename a directory

**Chemin :** File Service › Operations on Directory Resource › Rename a directory

URL — /fileservice/{device|environment_variable}/{directory}

**URL :** `/fileservice/{device|environment_variable}/{directory}`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
fs-newname
=The new directory name fs-get-directory-actions
Required
fs-action
=rename
Required
```

**Success :** HTTP_OK(200)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415), METHOD_NOT_ALLOWED(405)
See
Robot controller return codes

**Sample Call :**
```bash
Rename a directory
curl --digest -u "Default User":robotics -d "fs-newname=newdir&fs-action=rename" -X POST "http://localhost/fileservice/$home/testdir"
```

**Notes :** Supported in bootserver mode

---

## Copy a directory

**Chemin :** File Service › Operations on Directory Resource › Copy a directory

URL — /fileservice/{device|environment_variable}/{directory}

**URL :** `/fileservice/{device|environment_variable}/{directory}`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
fs-overwrite
= true|false defaults to false. fs-get-directory-actions
Required
fs-newname
= The new directory name. See
Notes
below.
Required
fs-action
=copy
Required
```

**Success :** NO_CONTENT(204)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415), CONFLICT(409)
See
Robot controller return codes

**Sample Call :**
```bash
Create a copy of a directory
curl --digest -u "Default User":robotics -d "fs-newname=newdir&fs-action=copy" -X POST "http://localhost/fileservice/$home/testdir"
```

**Notes :** The value for
fs-newname
can either be absolute or relative. It is differentiated based on whether the value has a leading slash (absolute) or not (relative).
Note: when absolute paths are used, it should start from /fileservice e.g.
Absolute path :
fs-newname=/fileservice/$home/copydir2
Relative to source path:
fs-newname=copydir2
Supported in bootserver mode

---

## Delete a directory

**Chemin :** File Service › Operations on Directory Resource › Delete a directory

URL — /fileservice/{device|environment_variable}/{directory}

**URL :** `/fileservice/{device|environment_variable}/{directory}`  
**Method :** `DELETE`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), BAD_REQUEST(400), METHOD_NOT_ALLOWED(405)
See
Robot controller return codes

**Sample Call :**
```bash
Delate a directory
curl --digest -u "Default User":robotics -X DELETE "http://localhost/fileservice/$home/testdir"
```

**Notes :** Supported in bootserver mode

---

## Operations on File Resource

**Chemin :** File Service › Operations on File Resource

---

## Get a file

**Chemin :** File Service › Operations on File Resource › Get a file

URL — /fileservice/{device}|{directory}/{file}

**URL :** `/fileservice/{device}|{directory}/{file}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404),
See
Robot controller return codes

**Sample Call :**
```bash
Get a file.
curl --digest -u "Default User":robotics "http://localhost/fileservice/$home/docs/test.txt"
```

**Notes :** Supported in bootserver mode

---

## Get File Actions

**Chemin :** File Service › Operations on File Resource › Get File Actions

URL — /fileservice/{device}|{directory}/{file}

**URL :** `/fileservice/{device}|{directory}/{file}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
Returns action Forms for this resource
```

**Data Params :**
```
None
```

**Actions :**
```
fs-rename
fs-newname
=[alphanumeric]
Required
fs-copy
fs-newname
=[alphanumeric]
Required
fs-overwrite
=[true|false]
Required
, Multiple selection
fs-upload
fs-filename
=[alphanumeric]
Required
fs-delete
Delete the file
```

**Success :** HTTP_OK(200)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), See
Robot controller return codes

**Sample Call :**
```bash
Get actions on a file.
curl --digest -u "Default User":robotics "http://localhost/fileservice/$home/docs/test.txt?action=show"
```

**Notes :** Supported in bootserver mode

---

## Rename a file

**Chemin :** File Service › Operations on File Resource › Rename a file

URL — /fileservice/{device|environment_variable|directory}/{file}

**URL :** `/fileservice/{device|environment_variable|directory}/{file}`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
fs-newname
=The new file name
Required
fs-action
=rename
Required
```

**Success :** NO_CONTENT(204)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
See
Robot controller return codes

**Sample Call :**
```bash
Rename a file
curl --digest -u "Default User":robotics -d "fs-newname=newfile.txt&fs-action=rename" -X POST "http://localhost/fileservice/$home/test.txt"
```

**Notes :** Supported in bootserver mode

---

## Create a copy of a file

**Chemin :** File Service › Operations on File Resource › Create a copy of a file

URL — /fileservice/{device|environment_variable}/{filename}

**URL :** `/fileservice/{device|environment_variable}/{filename}`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
fs-overwrite
= true|false defaults to false.
fs-newname
= The new file name. See Notes below.
Required
fs-action
=copy
Required
```

**Success :** NO_CONTENT(204)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), BAD_REQUEST(400), UNSUPPORTED_MEDIA(415), CONFLICT(409)
See
Robot controller return codes

**Sample Call :**
```bash
Create a copy of a file
curl --digest -u "Default User":robotics -d "fs-newname=newfile.txt&fs-action=copy" -X POST "http://localhost/fileservice/$home/file.txt"
```

**Notes :** The value for
fs-newname
can either be absolute or relative. It is differentiated based on the whether the value has a leading slash (absolute) or not (relative).
Note: when absolute paths are used, it should start from /fileservice e.g.
Absolute path :
fs-newname=/fileservice/$home/copyfile2.txt
Relative to source path:
fs-newname=copyfile2.txt
Supported in bootserver mode
Maximum supported file size is less than 2GB.

---

## Upload a file

**Chemin :** File Service › Operations on File Resource › Upload a file

URL — /fileservice/{device|environment_variable|directory}/{file}

**URL :** `/fileservice/{device|environment_variable|directory}/{file}`  
**Method :** `PUT`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
The file content
```

**Success :** HTTP_OK(200), CREATED(201)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), FORBIDDEN(403), BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Upload a file
curl --digest -u "Default User":robotics -d -X PUT "http://localhost/fileservice/$home/test.txt"
```

**Notes :** If the file exists, the file is overwritten with the specified content else a new file with the given name is created.
Supported in bootserver mode
Maximum supported file size is less than 800MB.

---

## Delete a file

**Chemin :** File Service › Operations on File Resource › Delete a file

URL — /fileservice/{device|environment_variable|directory}/{file}

**URL :** `/fileservice/{device|environment_variable|directory}/{file}`  
**Method :** `DELETE`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), BAD_REQUEST(400),METHOD_NOT_ALLOWED(405)
See
Robot controller return codes

**Sample Call :**
```bash
Delete a file
curl --digest -u "Default User":robotics -X DELETE "http://localhost/fileservice/$home/test.txt"
```

**Notes :** Supported in bootserver mode

---

## Get file Meta data

**Chemin :** File Service › Operations on File Resource › Get file Meta data

URL — /fileservice/{device|environment_variable|directory}/{file}

**URL :** `/fileservice/{device|environment_variable|directory}/{file}`  
**Method :** `HEAD`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)

**Error :** UNAUTHORIZED(401), NOT_FOUND(404), See
Robot controller return codes

**Sample Call :**
```bash
Delete a file
curl --digest -u "Default User":robotics -X HEAD "http://localhost/fileservice/$home/test.txt"
```

**Notes :** Supported in bootserver mode

---

## RobotWare Services

**Chemin :** RobotWare Services

---

## Get RobotWare services

**Chemin :** RobotWare Services › Get RobotWare services

URL — /rw

**URL :** `/rw`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
rwservice-li
- RobotWare service item
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw"
```

**Notes :** Supported in bootserver mode

---

## CFG Service

**Chemin :** RobotWare Services › CFG Service

---

## Get CFG resources

**Chemin :** RobotWare Services › CFG Service › Get CFG resources

URL — /rw/cfg

**URL :** `/rw/cfg`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
cfg-domain-li
Specifies a link to the 'cfg-domain` resource.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/cfg
"
```

**Notes :** Not supported in bootserver mode

---

## Get CFG actions

**Chemin :** RobotWare Services › CFG Service › Get CFG actions

URL — /rw/cfg

**URL :** `/rw/cfg`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
validate
- Validate a configuration file before loading. Inspecting a CFG file for any errors that would occur during a load of the file, including checking for duplicate instance-names.
filepath
=[file path]
Required
, RobotWare environ variables such as $HOME, $TEMP can be used in the filepath.
action-type
=[add | replace | add-with-reset]
Required
, Multiple selection
add
- Load a configuration file as external, i.e., instances will not be write-protected. If any instance in the file already exists, the file will not be loaded and an error code is returned.
replace
- As
add
, but the cfg-domain is reset before loading
add-with-reset
- Add the instances in the given file to the database. In case of instance name conflicts, the new instances replaces the existing.
load
- Load a CFG configuration file.
filepath
=[file path]
Required
, RobotWare environ variables such as $HOME, $TEMP can be used in the filepath.
action-type
=[add | replace | add-with-reset]
Required
, Multiple selection. See validate.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Retrieve actions on the CFG resource
curl --digest -u "Default User":robotics" "
http://localhost/rw/cfg?action=show
"
Validate CFG file before load
curl --digest -u "Default User":robotics -d "filepath=$TEMP/a.cfg&action-type=add-with-reset" -X POST "http://localhost/rw/cfg?action=validate"
Load CFG file
curl --digest -u "Default User":robotics -d "filepath=$TEMP/a.cfg&action-type=add-with-reset" -X POST "http://localhost/rw/cfg?action=load"
```

**Notes :** Not supported in bootserver mode

---

## Validate CFG file

**Chemin :** RobotWare Services › CFG Service › Validate CFG file

URL — /rw/cfg

**URL :** `/rw/cfg`  
**Method :** `POST`

**URL Params :**
```
action=validate
Required
See
Common URL parameters
```

**Data Params :**
```
filepath
File on controller to validate, see
Get CFG actions
action-type
=[add | replace | add-with-reset] Validation method, see
Get CFG actions
```

**Resources :**
```
cfg-validate
Validate a configuration file before loading. Inspecting a CFG file for any errors that would occur during a load of the file, including checking for duplicate instance-names.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
see
HTTP Status codes
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "filepath=$TEMP/a.cfg&action-type=add-with-reset" -X POST "http://localhost/rw/cfg?action=validate"
```

**Notes :** Not supported in bootserver mode

---

## Load CFG file

**Chemin :** RobotWare Services › CFG Service › Load CFG file

URL — /rw/cfg

**URL :** `/rw/cfg`  
**Method :** `POST`

**URL Params :**
```
action=load
Required
See
Common URL parameters
```

**Data Params :**
```
filepath
File on controller to load, see
Get CFG actions
action-type
=[add | replace | add-with-reset] Validation method, see
Get CFG actions
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "filepath=$TEMP/a.cfg&action-type=add-with-reset" -X POST "http://localhost/rw/cfg?action=load"
```

**Notes :** Not supported in bootserver mode

---

## Validate CFG Instance before Delete

**Chemin :** RobotWare Services › CFG Service › Validate CFG Instance before Delete

URL — /rw/cfg

**URL :** `/rw/cfg`  
**Method :** `POST`

**URL Params :**
```
action=validate-inst-at-del
Required
```

**Data Params :**
```
name={instance name}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), NOT_FOUND(404), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=abc" -X POST "http://localhost/rw/cfg?action=validate-inst-at-del"
```

**Notes :** Not supported in bootserver mode

---

## Validate CFG Instances

**Chemin :** RobotWare Services › CFG Service › Validate CFG Instances

URL — /rw/cfg

**URL :** `/rw/cfg`  
**Method :** `POST`

**URL Params :**
```
action=validate-instances
Required
```

**Data Params :**
```
operation={0 | 1}
Optional
0 represents add and 1 represents delete. Default value is 0.
cfgdomain={configuration domain}
Required
cfgtype={configuration type}
Required
instances={instance names}
Required
instancescount={instances count}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), NOT_FOUND(404), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "operation=1&cfgdomain=I/O&cfgtype=DeviceNetDevice&instances=TestingValid1&instancescount=1" -X POST "http://localhost/rw/cfg?action=validate-instances"
```

**Notes :** Not supported in bootserver mode

---

## Keyless motor ON

**Chemin :** RobotWare Services › CFG Service › Keyless motor ON

URL — /rw/cfg

**URL :** `/rw/cfg`  
**Method :** `POST`

**URL Params :**
```
action=keyless
Required
```

**Data Params :**
```
state=run
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "state=run" -X POST "http://localhost/rw/cfg?action=keyless"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on cfg ChangeCount

**Chemin :** RobotWare Services › CFG Service › Subscribe on cfg ChangeCount

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
Required
*<identifier>*=The subscription resource URI (The URI here is: '/rw/cfg')
Required
*<identifier>-p*=The priority associated with the subscription resource.
Required
```

**Resources :**
```
cfg-prop-ev
change-count
Change count
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on cfg change count
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/cfg&1-p=0" "http://localhost/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/cfg&1-p=1" "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode.

---

## Operations on CFG domain

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain

---

## Get CFG Domain Types

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Get CFG Domain Types

URL — /rw/cfg/{domain}

**URL :** `/rw/cfg/{domain}`  
**Method :** `GET`

**URL Params :**
```
start={start value} start Page number
limit={limit value} limit Number of elements to retrieve(maximum/default value of limit is 70)
See Common URL parameters
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
next
Link to next page (Will be absent if there is no next page)
first
Link to first page (Will be only present on last page)
cfg-dt-li
Cfg domain type list item, specifies a link to the detailed
cfg-domain-type
resource.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/cfg/moc"
```

**Notes :** Not supported in bootserver mode

---

## Get Actions on a CFG domain

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Get Actions on a CFG domain

URL — /rw/cfg/{domain}

**URL :** `/rw/cfg/{domain}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
saveas
- Save the CFG domain to the given file.
filepath
=[file path]
Required
reset
- Remove all external instances in a CFG domain.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Get actions supported by a CFG domain
curl --digest -u "Default User":robotics "http://localhost/rw/cfg/sio?action=show"
Save the CFG domain to the given file.
curl --digest -u "Default User":robotics -d "filepath=/fileservice/$HOME/a.cfg" -X POST "http://localhost/rw/cfg/sio?action=saveas"
Remove all external instances in a CFG domain
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/cfg/sio?action=reset"
```

**Notes :** CFG Mastership is handled internally if not explicit held by the client.
Not supported in bootserver mode

---

## Save CFG domain

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Save CFG domain

URL — /rw/cfg/{domain}

**URL :** `/rw/cfg/{domain}`  
**Method :** `POST`

**URL Params :**
```
action=saveas
Required
See
Common URL parameters
```

**Data Params :**
```
filepath
Required
File on controller to load
save-mode
Optional
{Normal | NormalEx | Internals | Types}
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403), UNAUTHORIZED(401)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Save the CFG domain to the given file
curl --digest -u "Default User":robotics -d "filepath=/fileservice/$HOME/a.cfg" -X POST "http://localhost/rw/cfg/sio?action=saveas"
```

**Notes :** Not supported in bootserver mode

---

## Reset CFG domain

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Reset CFG domain

URL — /rw/cfg/{domain}

**URL :** `/rw/cfg/{domain}`  
**Method :** `POST`

**URL Params :**
```
action=reset
Required
see
Get Actions on a CFG domain
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Remove all external instances in a CFG domain
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/cfg/sio?action=reset"
```

**Notes :** Not supported in bootserver mode

---

## Operations on CFG type

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type

---

## Get CFG type

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Get CFG type

URL — /rw/cfg/{domain}/{type}

**URL :** `/rw/cfg/{domain}/{type}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
cfg-dt-attributes-li
Specifies a link to the 'cfg-domain-type-attributes` resource.
cfg-no-of-attributes
Number of attributes for instance.
cfg-dt-instances-li
Specifies a link to the detailed
cfg-domain-type-instances
resource.
cfg-no-of-instances
Total number of instances in domain type.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT_FOUND(404)

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/cfg/eio/INDUSTRIAL_NETWORK"
```

**Notes :** Not supported in bootserver mode

---

## Operations on CFG attributes

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG attributes

---

## Get all attributes of the given domain type

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG attributes › Get all attributes of the given domain type

URL — /rw/cfg/{domain}/{type}/attributes

**URL :** `/rw/cfg/{domain}/{type}/attributes`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
cfg-dt-attribute-li
name
=[string] Attribute name.
type
=[string] The type of attribute. Can be {char | string | long | ulong | short | ushort | bool | float | byte}.
numbers
=[numeric] Array size if an array, otherwise 1
mini
=[alphanumeric] Min value for range checking. The min length, if the attribute is a string.
max
=[alphanumeric] Max value for range checking. The max length, if the attribute is a string.
init
=[aplhanumeric] Default value of this attribute
mandatory
=[true|false] A boolean indicating if this attribute is mandatory.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/cfg/eio/INDUSTRIAL_NETWORK/attributes"
```

**Notes :** Not supported in bootserver mode

---

## Operations on CFG instances

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances

---

## Get all instances of the given domain type

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Get all instances of the given domain type

URL — /rw/cfg/{domain}/{type}/instances

**URL :** `/rw/cfg/{domain}/{type}/instances`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
cfg-dt-instance-li
Cfg instance
rdonly
={true|false} Specifies if the instance is readonly.
title
Instance name
instanceid
Public id for instance
cfg-ia-t-li
Cfg instance
value
Attribute value.
title
Attribute name.
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/cfg/eio/EIO_BUS/instances"
```

**Notes :** Not supported in bootserver mode

---

## Get actions on CFG instances

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Get actions on CFG instances

URL — /rw/cfg/{domain}/{type}/instances

**URL :** `/rw/cfg/{domain}/{type}/instances`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
reset
- Remove all external (non-readonly) instances of a type
create-default
- Create an external instance with default values.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/cfg/eio/INDUSTRIAL_NETWORK/instances?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Reset CFG instances

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Reset CFG instances

URL — /rw/cfg/{domain}/{type}/instances

**URL :** `/rw/cfg/{domain}/{type}/instances`  
**Method :** `POST`

**URL Params :**
```
action=reset
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Reset CFG instances
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/cfg/eio/INDUSTRIAL_NETWORK/instances?action=reset"
```

**Notes :** Not supported in bootserver mode

---

## Create default CFG instance

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Create default CFG instance

URL — /rw/cfg/{domain}/{type}/instances

**URL :** `/rw/cfg/{domain}/{type}/instances`  
**Method :** `POST`

**URL Params :**
```
action=create-default
Required
See
Common URL parameters
```

**Data Params :**
```
name
name of instance
Required
see
Get actions on CFG instances
```

**Resources :**
```
instancename
Created Instance name.
instancename
Created Instance Id.
```

**Success :** CREATED(201)
Location header: instances/{instancename}
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Create default CFG instance
curl --digest -u "Default User":robotics -d "name=testinstance" -X POST "http://localhost/rw/cfg/eio/INDUSTRIAL_NETWORK/instances?action=create-default"
```

**Notes :** Use location header to fetch information about newly created resource.
Not supported in bootserver mode

---

## Operations on CFG instance

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Operations on CFG instance

---

## Get CFG instance

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Operations on CFG instance › Get CFG instance

URL — /rw/cfg/{domain}/{type}/instances/{instance name}

**URL :** `/rw/cfg/{domain}/{type}/instances/{instance name}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
cfg-dt-instance-li
List of attributes for the given type
rdonly
If true is the instance read only
title
Name of the instance
instanceid
Public id for instance
cfg-ia-t-li
Attribute of the instance
value
Value of the atribute
title
Name of the attribute
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/cfg/sys/PRESENT_OPTIONS/instances/sis
"
```

**Notes :** Not supported in bootserver mode

---

## Get CFG instance actions

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Operations on CFG instance › Get CFG instance actions

URL — /rw/cfg/{domain}/{type}/instances/{instance}

**URL :** `/rw/cfg/{domain}/{type}/instances/{instance}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set
- Update one or more attributes
name
- Name
desc
- Description
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/cfg/eio/eio_bus/instances?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Update CFG instance

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Operations on CFG instance › Update CFG instance

URL — /rw/cfg/{domain}/{type}/instances/{instance}

**URL :** `/rw/cfg/{domain}/{type}/instances/{instance}`  
**Method :** `POST`

**URL Params :**
```
action=set
```

**Data Params :**
```
{attribute name}={attribute value}
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Update one or more attributes
curl --digest - u "Default User" : robotics -d "Simulated=True" - X POST "http://localhost/rw/cfg/eio/INDUSTRIAL_NETWORK/instances/testinstance?action=set"
```

**Notes :** Not supported in bootserver mode

---

## Delete CFG instance

**Chemin :** RobotWare Services › CFG Service › Operations on CFG domain › Operations on CFG type › Operations on CFG instances › Operations on CFG instance › Delete CFG instance

URL — /rw/cfg/{domain}/{type}/instances/{instance}

**URL :** `/rw/cfg/{domain}/{type}/instances/{instance}`  
**Method :** `DELETE`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
Delete CFG instance
curl --digest -u "Default User":robotics - X DELETE "http://localhost/rw/cfg/eio/INDUSTRIAL_NETWORK/instances/testinstance"
```

**Notes :** Not supported in bootserver mode

---

## DIPC service

**Chemin :** RobotWare Services › DIPC service

---

## Get DIPC Resources

**Chemin :** RobotWare Services › DIPC service › Get DIPC Resources

URL — /rw/dipc

**URL :** `/rw/dipc`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
dipc-info-li
max-body-size
=[numeric], the maximum data size that can sent over a DIPC queue
max-pkg-size
=[numeric], the maximum package size that can sent over a DIPC queue
dipc-queue-li
Specifies a link to the detailed
dipc-queue
resource.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/dipc"
```

**Notes :** Not supported in bootserver mode

---

## Get DIPC Actions

**Chemin :** RobotWare Services › DIPC service › Get DIPC Actions

URL — /rw/dipc

**URL :** `/rw/dipc`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
dipc-create
dipc-queue-name
=[alphanumeric]
Required
, The name of queue
dipc-queue-size
=[anumeric]
Required
, The size of queue
dipc-max-msg-size
=[anumeric]
Required
, The mazimum message size allowed in queue. Create a queue.
subscribe
Subscription Parameters**
dipc-subscribe
Subscribe on DIPC queues
sub-res
subscription resource
resources
resources
selected
selected
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/dipc?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Create a queue

**Chemin :** RobotWare Services › DIPC service › Create a queue

URL — /rw/dipc

**URL :** `/rw/dipc`  
**Method :** `POST`

**URL Params :**
```
action=dipc-create
Required
```

**Data Params :**
```
dipc-queue-name
The name of the queue
Required
dipc-queue-size
The queue size supports a minimum value of 1 and maximum value of 32767
Required
dipc-max-msg-size
The message size supports a minimum value of 1 and maximum value of 444
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Restart controller with the specified mode
curl --digest -u "Default User":robotics -d "dipc-queue-name=testq&dipc-queue-size=200&dipc-max-msg-size=50" -X POST "http://localhost/rw/dipc?action=dipc-create"
```

**Notes :** Not supported in bootserver mode

---

## Operations on DIPC Queue

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue

---

## Get DIPC Queue

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue › Get DIPC Queue

URL — /rw/dipc/{queue-name}

**URL :** `/rw/dipc/{queue-name}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
dipc-queue
The operation mode
testq
Test queue
queue-size
The queue size
queue-name
The queue name to create
queue-max-msg-size
The maximum message size
queue-slot-id
The queue slot id
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/dipc/testq"
```

**Notes :** Not supported in bootserver mode

---

## Get DIPC Queue Actions

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue › Get DIPC Queue Actions

URL — /rw/dipc/{queue-name}

**URL :** `/rw/dipc/{queue-name}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
dipc-send
Send a message to a queue
dipc-src-queue-name
The source queue name
dipc-cmd
The dipc command parameter
dipc-userdef
The dipc user def parameter
dipc-msgtype
The dipc message type parameter, should 0 or 1
dipc-data
The data to send
testq
Test queue
PyInternalslot0
Internal slot
PyExternalslot1
External slot
RimDispatcher
Dispatcher
dipc-subscribe
Subscribe on queue
sub-res
subscription resource
resources
resources
selected
selected
dipc-delete
Delete the queue
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X DELETE "http://localhost/rw/dipc/testq?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Send message

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue › Send message

URL — /rw/dipc/{queue-name}

**URL :** `/rw/dipc/{queue-name}`  
**Method :** `POST`

**URL Params :**
```
action=dipc-send
Required
```

**Data Params :**
```
dipc-src-queue-name
The source queue name
Required
dipc-cmd
The dipc command parameter
Required
dipc-userdef
The dipc user def parameter
Required
dipc-msgtype
The dipc message type parameter, should 0 or 1.0 for message & 1 for package
Required
dipc-data
The data to send
Required
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Send message to queue
curl --digest -u "Default User":robotics -d "dipc-src-queue-name=testq&dipc-cmd=111&dipc-userdef=222&dipc-msgtype=1&dipc-data=hello" -X POST "http://localhost/rw/dipc/testq?action=dipc-send"
```

**Notes :** Not supported in bootserver mode

---

## Read message

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue › Read message

URL — /rw/dipc/{queue-name}

**URL :** `/rw/dipc/{queue-name}`  
**Method :** `GET`

**URL Params :**
```
action=dipc-read
Required
timeout={timeout in ms} (default 0)
Optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
dipc-read-li
queue-name
The queue name to create
queue-size
The queue size
queue-sid
The slot id of the current queue
queue-did
The slot id of the queue that write the data
dipc-msgtype
Message type. Can be either IPC_PACKAGE|IPC_SEND (1 or 0 in DIPC Send)
dipc-cmd
The dipc command
dipc-userdef
Userdef
dipc-data
The queue data
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/dipc/testq?action=dipc-read"
```

**Notes :** Not supported in bootserver mode.

---

## Delete DIPC Queue

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue › Delete DIPC Queue

URL — /rw/dipc/{queue-name}

**URL :** `/rw/dipc/{queue-name}`  
**Method :** `DELETE`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Delete a queue
curl --digest -u "Default User":robotics -X DELETE "http://localhost/rw/dipc/testq"
```

**Notes :** Not supported in bootserver mode
User can delete DIPC queue only if the queue is created by the same user

---

## Subscribe DIPC Queue

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue › Subscribe DIPC Queue

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/dipc/{queue-name}')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
dipc-msg-ev
Message in queue
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on queue
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/dipc/testq&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/dipc/testq&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe DIPC Queue without reading message

**Chemin :** RobotWare Services › DIPC service › Operations on DIPC Queue › Subscribe DIPC Queue without reading message

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/dipc/{queue-name};nomessage')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
dipc-msg-ev
Message in queue
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on queue
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/dipc/testq;nomessage&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/dipc/testq;nomessage&1-p=1" -X POST "http://localhost/subscription"
Notes
        -----

        Not supported in bootserver mode
```

---

## Elog service

**Chemin :** RobotWare Services › Elog service

---

## Get Elog Resources

**Chemin :** RobotWare Services › Elog service › Get Elog Resources

URL — /rw/elog

**URL :** `/rw/elog`  
**Method :** `GET`

**URL Params :**
```
lang=[language-code]
Optional
, a two letter language code e.g. en, sv, de, hi etc.
In addition to returning a list of all elog domain, this option returns all the domain names in the specified language.
example: lang=de
resource=count
Optional
In addition to returning a list of all elog domain, this option returns the number of elog messages in each elog domain.
example: resource=count
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
elog-domain-li
Specifies a link to the 'elog-domain` resource.
domain-name
=[alphanumeric] The domain name in the specified language. Available only when lang=xx query parameter is sent.
numevts
=[numeric] The number of elog messages in the elog domain. Available only when resource=count query parameter is sent.
buffsize
=[numeric] The elog buffer size of elog domain.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/elog"
curl --digest -u "Default User":robotics "http://localhost/rw/elog?lang=de"
```

**Notes :** Not supported in bootserver mode.

---

## Get Elog Actions

**Chemin :** RobotWare Services › Elog service › Get Elog Actions

URL — /rw/elog

**URL :** `/rw/elog`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
clearall
Clear elog messages in all elog domains
saveraw
Dump raw elog messages to a file.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/elog?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Clear elog messages

**Chemin :** RobotWare Services › Elog service › Clear elog messages

URL — /rw/elog

**URL :** `/rw/elog`  
**Method :** `POST`

**URL Params :**
```
action=clearall
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415),BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Clear all elog messages
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/elog?action=clearall"
```

**Notes :** Not supported in bootserver mode

---

## Save elog in system dump format

**Chemin :** RobotWare Services › Elog service › Save elog in system dump format

Description — Save event log in sys dump format on controller

**URL :** `/rw/elog`  
**Method :** `POST`

**URL Params :**
```
action=saveraw
Required
```

**Data Params :**
```
path={path along with file-name which will contain the system dump} Environment variables such as $system, $syspar shall be possible to have in the path.
```

**Success :** ACCEPTED (202)
Location header: /progress/{id}
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
Generate elog in system dump format.
curl --digest -u "Default User":robotics -d "path=/fileservice/$syspar/elog_dump.txt" -X POST "http://localhost/rw/elog?action=saveraw"
```

**Notes :** Since saving an elog in system dump format is an asynchronous task, the value of location header can be subscribed on to get information about the status of the task.

---

## Operations on elog domain

**Chemin :** RobotWare Services › Elog service › Operations on elog domain

---

## Get elog messages in domain

**Chemin :** RobotWare Services › Elog service › Operations on elog domain › Get elog messages in domain

URL — /rw/elog/{domain-number}

**URL :** `/rw/elog/{domain-number}`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
lang
=[alphanumeric]
Optional
, a two letter language code e.g. en, sv, de, hi etc.
This option returns all the elog messages in the specified language.
example: lang=de
resource
={count|info|title}**Optional**
count
Returns the number of events in the given domain.
example: resource=count
info
In addition to returning a list of all elog domain, this option returns the size of elog buffer and Number of event logs for each elog domain.
example: resource=info
title
When this parameter is provided, only the elog message title is returned. Allowed only along with
lang
query parameter.
example: lang=de&resource=title
order
={lifo|fifo}
Optional
Return the elog messages in fifo or lifo order
example: order=fifo
elogseqnum
=[numeric]
Optional
Return the elog messages starting from the specified sequence number
example: elogseqnum=8
```

**Data Params :**
```
None
```

**Resources :**
```
elog-message-li
msg-type
=[numeric]{0|1|2|3}** The elog message type
0
Any event type. For search and trigger conditions only. Cannot be used when writing an event.
1
State change, or informational event.
2
Warning Event
3
Error Event.
code
=[numeric] The elog message code
src-name
=[numeric] The elog message source
tstamp
=[datetime] The time stamp when the event log was generated
argc
=[numeric] The number of arguments present in this elog message
arg[n], type
=[numeric] The argument's position e.g. arg1, arg2 etc..The type of argument can be float, string or long
title
=[alphanumeric] The elog message title in the specified langauge. Available only when
lang
parameter is provided
desc
=[alphanumeric] The elog message description in the specified langauge. Available only when
lang
parameter is provided
conseqs
=[alphanumeric] The elog message consequences in the specified langauge. Available only when
lang
parameter is provided
causes
=[alphanumeric] The elog message causes in the specified langauge. Available only when
lang
parameter is provided
actions
=[alphanumeric] The elog message actions in the specified langauge. Available only when
lang
parameter is provided
elog-domain
numevts
=[numeric] The number of elog messages in this domain
buffsize
=[numeric] Size of elog buffer for this domain
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0"
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0?resource=count"
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0?lang=de&amp;resource=title"
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0?lang=de"
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0?order=fifo"
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0?elogseqnum=8"
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0?resource=info"
```

**Notes :** Not supported in bootserver mode

---

## Get Actions on elog domain

**Chemin :** RobotWare Services › Elog service › Operations on elog domain › Get Actions on elog domain

URL — /rw/elog/{domain-number}

**URL :** `/rw/elog/{domain-number}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
clear
Clear elog messages in this domain
subscribe
Subscribe on a elog domain
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Clear elog messages

**Chemin :** RobotWare Services › Elog service › Operations on elog domain › Clear elog messages

URL — /rw/elog/{domain-number}

**URL :** `/rw/elog/{domain-number}`  
**Method :** `POST`

**URL Params :**
```
action=clear
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400), NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
Clear all elog messages
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/elog/0?action=clear"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on elog domain

**Chemin :** RobotWare Services › Elog service › Operations on elog domain › Subscribe on elog domain

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/elog/{0}')
Required
<identifier>-p = The priority associated with the subscription resource.
Required
```

**Resources :**
```
elog-message-ev
seqnum
The sequence number of the event
href self
Link to the event string
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on elog domain 0
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/elog/0&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/elog/0&1-p=1" -X POST "http://localhost/subscription"
The subscription request will return a message similar to the sample response above. To retrieve the elog text must the client do a GET on the link returned in the elog-message-ev.
```

**Notes :** Not supported in bootserver mode

---

## Operations on elog domain message

**Chemin :** RobotWare Services › Elog service › Operations on elog domain › Operations on elog domain message

---

## Get Elog Message in domain

**Chemin :** RobotWare Services › Elog service › Operations on elog domain › Operations on elog domain message › Get Elog Message in domain

URL — /rw/elog/{domain-number}/{sequence-number}

**URL :** `/rw/elog/{domain-number}/{sequence-number}`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
lang=[alphanumeric]
Optional
, a two letter language code e.g. en, sv, de, hi etc.
This option returns all the elog messages in the specified language.
example: lang=de
```

**Data Params :**
```
None
```

**Resources :**
```
elog-message
Specifies a link to the 'elog-domain` resource.
msg-type
=[numeric]{0|1|2|3}** The elog message type
0
Any event type. For search and trigger conditions only. Cannot be used when writing an event.
1
State change, or informational event.
2
Warning Event
3
Error Event.
code
=[numeric] The elog message code
src-name
=[numeric] The elog message source
tstamp
=[datetime] The time stamp when the event log was generated
argc
=[numeric] The number of arguments present in this elog message
arg[n], type
=[numeric] The argument position e.g. arg1, arg2, .... The type of argument, can be string, long or float.
title
=[alphanumeric] The elog message title in the specified langauge. Available only when
lang
parameter is provided
desc
=[alphanumeric] The elog message description in the specified langauge. Available only when
lang
parameter is provided
conseqs
=[alphanumeric] The elog message consequences in the specified langauge. Available only when
lang
parameter is provided
causes
=[alphanumeric] The elog message causes in the specified langauge. Available only when
lang
parameter is provided
actions
=[alphanumeric] The elog message actions in the specified langauge. Available only when
lang
parameter is provided
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT_FOUND(404), BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/elog/0/8?lang=en"
```

**Notes :** Not supported in bootserver mode

---

## IO Service

**Chemin :** RobotWare Services › IO Service

---

## Get IO System resources

**Chemin :** RobotWare Services › IO Service › Get IO System resources

URL — /rw/iosystem

**URL :** `/rw/iosystem`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-networks-li
Networks list item
ios-devices-li
Devices list item
ios-signals-li
Signals list item
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem"
```

**Notes :** Not supported in bootserver mode

---

## Operations on IO Networks

**Chemin :** RobotWare Services › IO Service › Operations on IO Networks

---

## Get IO Networks resources

**Chemin :** RobotWare Services › IO Service › Operations on IO Networks › Get IO Networks resources

URL — /rw/iosystem/networks

**URL :** `/rw/iosystem/networks`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-network-li
name
Name of the IO-network
pstate
Physical state of the network: {halted, running, error, startup, init, unknown}
lstate
Logical state: {started, stopped, unknown}
rel
devices Link to devices connected to this network
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/networks"
```

**Notes :** Not supported in bootserver mode

---

## Get Actions on IO Networks

**Chemin :** RobotWare Services › IO Service › Operations on IO Networks › Get Actions on IO Networks

URL — /rw/iosystem/networks

**URL :** `/rw/iosystem/networks`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
search
Search IO networks based on name or state
name
The name of the network e.g. Virtual, Local etc.
pstate
The network state e.g. running
lstate
The logical state of the device
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/networks?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Search IO Networks

**Chemin :** RobotWare Services › IO Service › Operations on IO Networks › Search IO Networks

URL — /rw/iosystem/networks

**URL :** `/rw/iosystem/networks`  
**Method :** `POST`

**URL Params :**
```
action=search
Required
```

**Data Params :**
```
name
The network name e.g. Virtual or Local
state
The network state e.g. running
Only one Data Param is
mandatory
("name (or) state") . Example: name=local&state=running (or) state=running
```

**Resources :**
```
ios-network-li
name
Name of the IO-network
pstate
Physical state of the network: {halted, running, error, startup, init, unknown}
lstate
Logical state
rel
devices Link to devices connected to this network
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Search IO Networks
curl --digest -u "Default User":robotics -d "name=Local&state=running" -X POST "http://localhost/rw/iosystem/networks?action=search"
```

**Notes :** Not supported in bootserver mode

---

## Operations on IO Network

**Chemin :** RobotWare Services › IO Service › Operations on IO Network

---

## Get IO Network

**Chemin :** RobotWare Services › IO Service › Operations on IO Network › Get IO Network

URL — /rw/iosystem/networks/{network}

**URL :** `/rw/iosystem/networks/{network}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-network
IO network resource
name
IO network name
pstate
Physical state {halted, running, error, startup, init, unknown}
lstate
Logical state: {started, stopped, unknown}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/networks/Local"
```

**Notes :** Not supported in bootserver mode

---

## Get IO Network actions

**Chemin :** RobotWare Services › IO Service › Operations on IO Network › Get IO Network actions

URL — /rw/iosystem/networks/{network}

**URL :** `/rw/iosystem/networks/{network}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set
Set network state
lstate
Logical state of the network {start | stop}
config
Set configuration type
config-type
Network configuration type {BITS,GROUPS,BOTH,SCAN,UNITS}
subscribe
Subscribe network state changes
resources
resource name
priority
priority associated with the resource
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/networks/Local?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Update IO Network

**Chemin :** RobotWare Services › IO Service › Operations on IO Network › Update IO Network

URL — /rw/iosystem/networks/{network}

**URL :** `/rw/iosystem/networks/{network}`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
```

**Data Params :**
```
lstate = Logical network state
Required
see
Get IO Network actions
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Set signal value
curl --digest -u "Default User":robotics -d "lstate=start" -X POST "http://localhost/rw/iosystem/networks/Local?action=set"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe IO Network

**Chemin :** RobotWare Services › IO Service › Operations on IO Network › Subscribe IO Network

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
ios-networkstate
lstate
Network logical state
pstate
Network physical state
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on IO Network
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/networks/Local;state&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/networks/Local;state&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Get IO Network Configuration Properties

**Chemin :** RobotWare Services › IO Service › Operations on IO Network › Get IO Network Configuration Properties

URL — /rw/iosystem/networks/{network}

**URL :** `/rw/iosystem/networks/{network}`  
**Method :** `GET`

**URL Params :**
```
resource=config
Required
configtype = {configtype_value}
Optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-network-config-runtime
IO network resource
networkname
IO network name
networktype
Network type {LOC, ...}
networkaddress
Industrial network address
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/networks/Local?resource=config&configtype=1"
```

**Notes :** "configtype_value" should be 1 (or) 2 (or) 3 (2= general configuration , 1 = runtime configuration, 3 = both)
Not supported in bootserver mode

---

## Update IO Network Configuration Type

**Chemin :** RobotWare Services › IO Service › Operations on IO Network › Update IO Network Configuration Type

URL — /rw/iosystem/networks/{network}

**URL :** `/rw/iosystem/networks/{network}`  
**Method :** `POST`

**URL Params :**
```
action=config
Required
```

**Data Params :**
```
config-type = Network configuration type {BITS,GROUPS,BOTH,SCAN,UNITS}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "config-type=BITS" -X POST "http://localhost/rw/iosystem/networks/Local?action=config"
```

**Notes :** Not supported in bootserver mode

---

## Operations on IO Devices

**Chemin :** RobotWare Services › IO Service › Operations on IO Devices

---

## Get IO Devices

**Chemin :** RobotWare Services › IO Service › Operations on IO Devices › Get IO Devices

URL — /rw/iosystem/devices

**URL :** `/rw/iosystem/devices`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-device-li
IO Device list item
name
IO device name
type
Device type
pstate
Physical state {deact, running, error, unconnect, unconfg, startup, init, unknown}
lstate
Logical state: {disabled, enabled, unknown}
address
device address
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices"
```

**Notes :** Not supported in bootserver mode

---

## Get Actions IO Devices

**Chemin :** RobotWare Services › IO Service › Operations on IO Devices › Get Actions IO Devices

URL — /rw/iosystem/devices

**URL :** `/rw/iosystem/devices`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
search
Search devices
name
The name of the device
pstate
The physical state of the device
lstate
The logical state of the device
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Search IO Devices

**Chemin :** RobotWare Services › IO Service › Operations on IO Devices › Search IO Devices

URL — /rw/iosystem/devices

**URL :** `/rw/iosystem/devices`  
**Method :** `POST`

**URL Params :**
```
action=search
Required
```

**Data Params :**
```
name = The device name e.g. DRV_1
lstate = The device logical state e.g. enabled
network = The device physical state e.g. DeviceNet
Optional
Device name (or) device lstate is needed for search
example: name=panel&lstate=enabled (or) lstate=enabled
```

**Resources :**
```
ios-device-li
IO Device list item
name
IO device name
pstate
Physical state {deact, running, error, unconnect, unconfg, startup, init, unknown}
lstate
Logical state: {disabled, enabled, unknown}
address
device address
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Search IO Devices
curl --digest -u "Default User":robotics -d "name=DRV_1&lstate=enabled&network=DeviceNet" -X POST "http://localhost/rw/iosystem/devices?action=search"
```

**Notes :** Not supported in bootserver mode

---

## Operations on IO Device

**Chemin :** RobotWare Services › IO Service › Operations on IO Device

---

## Get IO Device

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Get IO Device

URL — /rw/iosystem/devices/{device}

**URL :** `/rw/iosystem/devices/{device}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-device
IO device resource
name
IO device name
pstate
Physical state {halted, running, error, startup, init, unknown}
lstate
Logical state: {enabled | disabled}
address
Device address
indata
In-put data for the device
inmask
In-put mask. Set bit to zero which indata shall not be set
outdata
Out-put data for the device
outmask
Out-put mask. Set bit to zero which outdata shall not be set
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices/Local/PANEL"
```

**Notes :** Not supported in bootserver mode

---

## Get IO Device actions

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Get IO Device actions

URL — /rw/iosystem/devices/{device}

**URL :** `/rw/iosystem/devices/{device}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set
Set device state
subscribe
Subscribe on devices state
lstate
Logical state: {enable | disable}
set-inputdata
Set input data
set-outputdata
Set output data
startbyte
Start byte of data
signaldata
Signal data
datamask
data mask
priority
priority associated with the resource
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices/Local/PANEL?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Update IO Device

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Update IO Device

URL — /rw/iosystem/devices/{device}

**URL :** `/rw/iosystem/devices/{device}`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
```

**Data Params :**
```
lstate = Logical device state
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Set signal value
curl --digest -u "Default User":robotics -d "lstate=enable" -X POST "http://localhost/rw/iosystem/devices/Local/DRV_1?action=set"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe IO Device

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Subscribe IO Device

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
ios-devicestate-ev
lstate
Device logical state
pstate
Device physical state
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on IO Device
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/devices/Local/PANEL;state&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/devices/Local/PANEL;state&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Set input data

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Set input data

URL — /rw/iosystem/devices/{device}

**URL :** `/rw/iosystem/devices/{device}`  
**Method :** `POST`

**URL Params :**
```
action=set-inputdata
Required
```

**Data Params :**
```
startbyte={indexnumber}
Required
signaldata={inputdata}
Required
datamask={datamask}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "startbyte=0&signaldata=100&datamask=255" -X POST "http://localhost/rw/iosystem/devices/Local/DRV_1?action=set-inputdata"
```

**Notes :** Only supported in Virtual Controller.
If input data is 4 bytes long, start byte can have values ranging from 0 to 3. Datamask/signal data can have values ranging from 0 to 255 (since it is accessed as 1 byte long). If datamask/signal data is greater than 255 (1 byte long), only first 8 bits is used.
Not supported in bootserver mode.

---

## Set output data

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Set output data

URL — /rw/iosystem/devices/{device}

**URL :** `/rw/iosystem/devices/{device}`  
**Method :** `POST`

**URL Params :**
```
action=set-outputdata
Required
```

**Data Params :**
```
startbyte={indexnumber}
Required
signaldata={inputdata}
Required
datamask={datamask}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "startbyte=0&signaldata=100&datamask=255" -X POST "http://localhost/rw/iosystem/devices/Local/DRV_1?action=set-outputdata"
```

**Notes :** Only supported in Virtual Controller.
If input data is 4 bytes long, start byte can have values ranging from 0 to 3. Datamask/signal data can have values ranging from 0 to 255 (since it is accessed as 1 byte long). If datamask/signal data is greater than 255 (1 byte long), only first 8 bits is used.
Not supported in bootserver mode.

---

## Get IO Device Configuration Properties

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Get IO Device Configuration Properties

URL — /rw/iosystem/devices/{device}

**URL :** `/rw/iosystem/devices/{device}`  
**Method :** `GET`

**URL Params :**
```
resource=config
Required
configtype = {configtype_value}
Optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-device-config-runtime
IO device resource
unitname
IO device name
networkname
Industrial network name
inputbits
Number of input bits on unit
outputbits
Number of output bits on unit
rapid
RAPID client in both manual or auto mode
localmanual
Local client in manual mode
localauto
Local client in auto mode
remotemanual
Remote client in manual mode
remoteauto
Remote client in auto mode
unitaddress
Device address
denydeactivate
lag indicating if possible to deactivate the I/O device or not
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices/DeviceNet/DN_Internal_Device?resource=config&configtype=1"
```

**Notes :** "configtype_value" should be 1 (or) 2 (or) 3 (2= general configuration , 1 = runtime configuration , 3 = both)
Not supported in bootserver mode

---

## Operations on eio Device

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Operations on eio Device

---

## Get eio device status information

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Operations on eio Device › Get eio device status information

URL — /rw/iosystem/devices/{network}/{device}/upgradeinfo

**URL :** `/rw/iosystem/devices/{network}/{device}/upgradeinfo`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
eio-device
Firmware upgrade info
state
Firmwawre status {0 | 1 | 2 | 3 | 4 | 5 | 10 | 11 | 15 | 20 | 25 | 30 | 40 | 45 | 50}
UNKNOWN = 0
AUTOMATIC = 1
MANUAL = 2
INFO = 3
ALLOCATE = 4
START = 5
RUNNING = 10
RUNNING_START_RECEIVED = 11
RUNNING_CHECK_IN_PROGRESS = 15
RUNNING_ERASE_IN_PROGRESS = 20
RUNNING_BURN_IN_PROGRESS = 25
RUNNING_END_RECEIVED = 30
CHECK = 40
DEALLOCATE = 45
FINISHED = 50
status
Firmwawre status {-1 | 0 | 1 | 2}
ERROR = -1
OK/FINISHED = 0
OK/UPGRADED = 1
PENDING = 2
program-name
Name of the installed program
serial-no
Serial no of the device
hw-revision
Hardware revision version
latest-program-name-available
Name of the latest installed program
```

**Success :** HTTP_OK(200), NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices/EtherNetIP/EN_Internal_Device/upgradeinfo"
```

**Notes :** Not supported in bootserver mode
Applicable only for RC

---

## Operations on Device Command

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Operations on Device Command

---

## Send Device Command

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Operations on Device Command › Send Device Command

URL — /rw/iosystem/devices/{device}/command

**URL :** `/rw/iosystem/devices/{device}/command`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
commandName = Name of the device command
Required
value = Command value
Required
valueLength = Number of bytes in command value
Required
timeout = Device timeout. Wait on answer from I/O device in maximum Timeout ms
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "commandName=FIRMWARE_INFO&value=0&valueLength=0&timeout=0" -X POST "http://localhost/rw/iosystem/devices/EtherNetIP/Local_IO/command"
```

**Notes :** Applicable only for RC.
Not supported in bootserver mode.

---

## Send Device Command actions

**Chemin :** RobotWare Services › IO Service › Operations on IO Device › Operations on Device Command › Send Device Command actions

URL — /rw/iosystem/devices/{device}/command

**URL :** `/rw/iosystem/devices/{device}/command`  
**Method :** `OPTIONS`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Actions :**
```
devicecommand
commandName
Name of the device command.
value
Command value.
valueLength
Number of bytes in command value.
timeout
Device timeout. Wait on answer from I/O device in maximum Timeout ms.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X OPTIONS "http://localhost/rw/iosystem/devices/EtherNetIP/Local_IO/command"
```

**Notes :** Not supported in bootserver mode.

---

## Operations on IO Signals

**Chemin :** RobotWare Services › IO Service › Operations on IO Signals

---

## Get IO Signals

**Chemin :** RobotWare Services › IO Service › Operations on IO Signals › Get IO Signals

URL — /rw/iosystem/signals

**URL :** `/rw/iosystem/signals`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-signal-li
IO-Signal list item
name
IO-signal name
type
Signal type {DO | DI | AO | AI | GI | GO}
category
Signals list item
lvalue
Signal value
lstate
Signals state {simulated | not simulated}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/signals"
```

**Notes :** Not supported in bootserver mode

---

## Signal Search

**Chemin :** RobotWare Services › IO Service › Operations on IO Signals › Signal Search

URL — /rw/iosystem/signals

**URL :** `/rw/iosystem/signals`  
**Method :** `POST`

**URL Params :**
```
action=signal-search
Required
start={start_value}
Optional
limit={limit_value}
Optional
```

**Data Params :**
```
name={signal_name}
Optional
device={device_name}
Optional
network={network_name}
Optional
category={category_name}
Optional
category-pon={categorypon_name}
Optional
type=DO | DI | AO | AI | GI | GO
Optional
invert=true | false
Optional
blocked=true | false
Optional
name2={signal_name}
Optional
device2={device_name}
Optional
network2={network_name}
Optional
category2={category_name}
Optional
category-pon2={categorypon_name}
Optional
type2=DO | DI | AO | AI | GI | GO
Optional
invert2=true | false
Optional
blocked2=true | false
Optional
```

**Resources :**
```
name
signal name
type
signal type
category
signal category
lvalue
signal logical value
lstate
signal logical state
start
element index
limit
Number of elements to read.
invert
Possible to combine two search criteria, where the signal is retrieved only if both are true. One of the criteria should have the invert set to TRUE, otherwise it is functionally identical to single search criteria.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** Bad Request(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "category=safety&type=DO" -X POST "http://localhost/rw/iosystem/signals?action=signal-search"
```

**Notes :** Not supported in bootserver mode

---

## Signal Search Extended

**Chemin :** RobotWare Services › IO Service › Operations on IO Signals › Signal Search Extended

URL — /rw/iosystem/signals

**URL :** `/rw/iosystem/signals`  
**Method :** `POST`

**URL Params :**
```
action=signal-searchex
Required
start={start_value}
limit={limit_value}
Optional
```

**Data Params :**
```
name={signal_name}
Optional
device={device_name}
Optional
network={network_name}
Optional
category={category_name}
Optional
category-pon={categorypon_name}
Optional
type=DO | DI | AO | AI | GI | GO
Optional
invert=true | false
Optional
blocked=true | false
Optional
name2={signal_name}
Optional
device2={device_name}
Optional
network2={network_name}
Optional
category2={category_name}
Optional
category-pon2={categorypon_name}
Optional
type2=DO | DI | AO | AI | GI | GO
Optional
invert2=true | false
Optional
blocked2=true | false
Optional
```

**Resources :**
```
name
signal name
type
signal type
category
signal category
lvalue
signal logical value
lstate
signal logical state
pvalue
signal physical value
quality
signal physical state
ltime-sec
logical time high
ltime-microsec
logical time low
ptime-sec
physical time high
ptime-microsec
physical time low
write-access-level
signal write access level
start
element index
limit
Number of elements to read.
invert
Possible to combine two search criteria, where the signal is retrieved only if both are true. One of the criteria should have the invert set to TRUE, otherwise it is functionally identical to single search criteria.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** Bad Request(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "category=safety&type=DO" -X POST "http://localhost/rw/iosystem/signals?action=signal-searchex"
```

**Notes :** Not supported in bootserver mode

---

## Unblock Signals

**Chemin :** RobotWare Services › IO Service › Operations on IO Signals › Unblock Signals

URL — /rw/iosystem/signals

**URL :** `/rw/iosystem/signals`  
**Method :** `POST`

**URL Params :**
```
action=unblock-signal
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** Bad Request(400), FORBIDDEN(403), UNAUTHORIZED(401)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/iosystem/signals?action=unblock-signal"
```

**Notes :** Not supported in bootserver mode

---

## Get IO Signals actions

**Chemin :** RobotWare Services › IO Service › Operations on IO Signals › Get IO Signals actions

URL — /rw/iosystem/signals

**URL :** `/rw/iosystem/signals`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** Bad Request(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/signals?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Operations on IO Signal

**Chemin :** RobotWare Services › IO Service › Operations on IO Signal

---

## Get an IO Signal

**Chemin :** RobotWare Services › IO Service › Operations on IO Signal › Get an IO Signal

URL — /rw/iosystem/signals/{network}/{unit}/{signal}

**URL :** `/rw/iosystem/signals/{network}/{unit}/{signal}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Resources :**
```
ios-signal
IO-signal resource
name
IO-signal name
type
Signal type {DO | DI | AO | AI | GI | GO}
category
A string defining which category the signal belongs to
lvalue
Logical Signal value
lstate
Signals state {simulated | not simulated}
unitnm
Name of the device the signal is connected to
phstate
Current physical state for the signal {invalid = EIO_SIGNAL_PHYSICAL_STATE_NOT_VALID , valid = EIO_SIGNAL_PHYSICAL_STATE_VALID
pvalue
Physical Signal value
ltime-sec
Logical Global time in sec
ltime-microsec
Logical Global time in micro sec
ptime-sec
Physical Global time in sec
ptime-microsec
Physical Global time in micro sec
quality
Signal quality
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/signals/Local/DRV_1/DRV1K1"
```

**Notes :** Not supported in bootserver mode.
/rw/iosystem/signals/{network}/{unit}/{signal};state will return only the IO signal value.

---

## Get IO Signal actions

**Chemin :** RobotWare Services › IO Service › Operations on IO Signal › Get IO Signal actions

URL — /rw/iosystem/signals/{network}/{unit}/{signal}

**URL :** `/rw/iosystem/signals/{network}/{unit}/{signal}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set
see
Update IO Signal Value
and see
Update IO Signal State
lstate
Signals state {simulated | not simulated}
lvalue
Logical Signal value
mode
Write mode, identifying type of value to write {value | invert | pulse | toggle | delay}
InputAsPhysical
Flag to write the input as physical {true | false}
Delay
Duration of delay in ms
Pulses
Number of pulses
ActivePulse
Number of Active pulses
PassivePulse
Number of Passive pulses
subscribe
see
Subscribe IO Signal
priority
priority associated with the resource
sub-signalstate
sub signal state
resources
resource
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/signals/Local/DRV_1/DRV1K1?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Update IO Signal State

**Chemin :** RobotWare Services › IO Service › Operations on IO Signal › Update IO Signal State

URL — /rw/iosystem/signals/{network}/{device}/{signal}

**URL :** `/rw/iosystem/signals/{network}/{device}/{signal}`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
```

**Data Params :**
```
lstate = Logical signal state {simulated | not simulated}
Required
see
Get IO Signal actions
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Set signal value
curl --digest -u "Default User":robotics -d "lstate=simulated" -X POST "http://localhost/rw/iosystem/signals/Local/DRV_1/DRV1K1?action=set"
```

**Notes :** Not supported in bootserver mode

---

## Update IO Signal Value

**Chemin :** RobotWare Services › IO Service › Operations on IO Signal › Update IO Signal Value

URL — /rw/iosystem/signals/{network}/{device}/{signal}

**URL :** `/rw/iosystem/signals/{network}/{device}/{signal}`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
```

**Data Params :**
```
lvalue
: logical signal value
Required
mode
: Write mode, identifying type of value to write {value | invert | pulse | toggle | delay}
value : Write supplied value.
invert: Inverts the signal.Only digital and group signals can be inverted.
pulse : Pulse the output according to parameter arguments.Only digital and group signals can be pulsed.
toggle: Pulse by toggling current signal value.Only digital and group signals can be toggle.
delay : Write supplied value using "queued delayed" mode.
Delay
: Delay time before activation, in ms
Pulses
: Number of pulses.Pulses is required if mode is toggle/pulse.
ActivePulse
: Active pulse length, in ms
PassivePulse
: Passive pulse length, in ms
userlog
: Log changes on controller {true | false), set if the setting shall be logged as Event log. Default value is 'false'
Its
mandatory
to give any one data param with its required combination.
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Notes :** Not supported in bootserver mode

---

## Subscribe IO Signal

**Chemin :** RobotWare Services › IO Service › Operations on IO Signal › Subscribe IO Signal

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
ios-signalstate-ev
lvalue
Signal value
lstate
Signals state {simulated | not simulated}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on IO-Signal, it is possible to subscribe with any subscription priority (i.e High,Medium,Low priority) on IO-Signals.
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/signals/Local/DRV_1/DRV1K1;state&1-p=2" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/signals/Local/DRV_1/DRV1K1;state&1-p=1" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/iosystem/signals/Local/DRV_1/DRV1K1;state&1-p=0" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Get IO signal Configuration Properties

**Chemin :** RobotWare Services › IO Service › Operations on IO Signal › Get IO signal Configuration Properties

URL — /rw/iosystem/signals/{network}/{unit}/{signal}

**URL :** `/rw/iosystem/signals/{network}/{unit}/{signal}`  
**Method :** `GET`

**URL Params :**
```
resource=config
Required
configtype = {configtype_value}
Optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ios-signal-config-runtime
IO-signal resource
signalname
Name of Signal
signalbits
Number of signal bits
rapid
RAPID client in both manual or auto mode
localmanual
Local client in manual mode
localauto
Local client in auto mode
remotemanual
Remote client in manual mode
remoteauto
Remote client in auto mode
setbydevicetransfer
The bit(s) in this signal is set by a device transfer operation
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/signals/Local/DRV_1/DRV1K1?resource=config&configtype=1"
```

**Notes :** "configtype_value" should be 1 (or) 2 (or) 3 (2= general configuration , 1 = runtime configuration , 3 = both)
Not supported in bootserver mode

---

## Mastership service

**Chemin :** RobotWare Services › Mastership service

---

## Get Mastership Resources

**Chemin :** RobotWare Services › Mastership service › Get Mastership Resources

URL — /rw/mastership

**URL :** `/rw/mastership`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
msh-resource-li
Provides link to the detailed
msh-resource
resource.
cfg = acquire mastership over configuration (cfg) domain
motion = acquire mastership over motion domain
rapid = acquire mastership over RAPID domain
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/mastership"
```

**Notes :** Not supported in bootserver mode

---

## Get Mastership Actions

**Chemin :** RobotWare Services › Mastership service › Get Mastership Actions

URL — /rw/mastership

**URL :** `/rw/mastership`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
request-mastership
Request mastership on all resources under mastership i.e. on CFG, MOTION and RAPID domains
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/mastership?action=request"
release-mastership
Release mastership on all resources under mastership i.e. on CFG, MOTION and RAPID domains
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/mastership?action=release"
subscribe
Subscribe on mastership request/release events on all domains.
e.g:
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/mastership/cfg&1-p=0&resources=2&2=/rw/mastership/rapid&2-p=0&resources=3&3=/rw/mastership/motion&3-p=0" -X POST "http://localhost/subscription"
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/mastership?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Mastership request

**Chemin :** RobotWare Services › Mastership service › Mastership request

URL — /rw/mastership

**URL :** `/rw/mastership`  
**Method :** `POST`

**URL Params :**
```
action=request
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Request mastership on all domains
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/mastership?action=request"
```

**Notes :** Not supported in bootserver mode
In manual mode, mastership can be gained after getting RMMP.

---

## Mastership release

**Chemin :** RobotWare Services › Mastership service › Mastership release

URL — /rw/mastership

**URL :** `/rw/mastership`  
**Method :** `POST`

**URL Params :**
```
action=release
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Release mastership on all domains
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/mastership?action=release"
```

**Notes :** Not supported in bootserver mode

---

## Mastership Subscribe

**Chemin :** RobotWare Services › Mastership service › Mastership Subscribe

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/mastership')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on mastership state changes
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/mastership&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/mastership&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Operations on Mastership domains

**Chemin :** RobotWare Services › Mastership service › Operations on Mastership domains

---

## Get Mastership Domain

**Chemin :** RobotWare Services › Mastership service › Operations on Mastership domains › Get Mastership Domain

URL — /rw/mastership/{domain-name}

**URL :** `/rw/mastership/{domain-name}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
msh-resource
The specified mastership resource.
uid = Unique User ID
location = Where the application is located.
alias = alternate name for the location.
application = the application holding the mastership in the domain.
mastership = Used to specify current master of a resource.
values of mastership are listed belows
nomaster - Mastership is not held.
remote - Mastership is held by a remote user.
local - Mastership is held by a local user, e.g., the GTPU.
internal - Mastership is held by an internal user (e.g., master of resource Jog is held during execution).
mastershipheldbyme = TRUE if the user holding the mastership is the user associated with the given client id (cid), FALSE otherwise.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/mastership/cfg"
```

**Notes :** Not supported in bootserver mode

---

## Get Mastership Domain Actions

**Chemin :** RobotWare Services › Mastership service › Operations on Mastership domains › Get Mastership Domain Actions

URL — /rw/mastership/{domain-name}

**URL :** `/rw/mastership/{domain-name}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
request-mastership
Request mastership on a particular resource.
e.g:
curl -X POST –digest -u "Default User":robotics "http://localhost/rw/mastership/cfg?action=request"
release-mastership
Release mastership on a particular resource.
e.g:
curl -X POST –digest -u "Default User":robotics "http://localhost/rw/mastership/cfg?action=release"
subscribe
Subscribe on mastership request/release events on a particular resource.
e.g:
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/mastership/cfg&1-p=0" -X POST "http://localhost/subscription"
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/mastership/cfg?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Mastership domain request

**Chemin :** RobotWare Services › Mastership service › Operations on Mastership domains › Mastership domain request

URL — /rw/mastership/{domain}

**URL :** `/rw/mastership/{domain}`  
**Method :** `POST`

**URL Params :**
```
action=request
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** NOT_FOUND(404)
FORBIDDEN(403)
BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Request mastership on cfg domain
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/mastership/cfg?action=request"
```

**Notes :** Not supported in bootserver mode
In manual mode, mastership can be gained after getting RMMP.

---

## Mastership Domain release

**Chemin :** RobotWare Services › Mastership service › Operations on Mastership domains › Mastership Domain release

URL — /rw/mastership/{domain}

**URL :** `/rw/mastership/{domain}`  
**Method :** `POST`

**URL Params :**
```
action=release
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** NOT_FOUND(404)
FORBIDDEN(403)
BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Release mastership on cfg domain
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/mastership/cfg?action=release"
```

**Notes :** Not supported in bootserver mode

---

## Mastership Domain Subscribe

**Chemin :** RobotWare Services › Mastership service › Operations on Mastership domains › Mastership Domain Subscribe

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/mastership')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
msh-resource-value
The mastership information
holdmastership = {1 | 0}, indicates if mastership is being held.
1 indicates TRUE
0 indicates FALSE
uid = unique user id
location = location where the user holding the mastership is present.
alias = alternate name
application = name of the application holding the mastership.
mastership = Used to specify current master of a resource.
values of mastership are listed belows
nomaster - Mastership is not held.
remote - Mastership is held by a remote user.
local - Mastership is held by a local user, e.g., the GTPU.
internal - Mastership is held by an internal user (e.g., master of resource Jog is held during execution).
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on cfg domain for changes
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/mastership/cfg&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/mastership/cfg&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Panel service

**Chemin :** RobotWare Services › Panel service

---

## Get Panel Resources

**Chemin :** RobotWare Services › Panel service › Get Panel Resources

URL — /rw/panel

**URL :** `/rw/panel`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
pnl-ctrlstate-li
The controller state resource
pnl-opmode-li
The Operation mode resource
pnl-speedratio-li
The Speed ratio resource
pnl-coldetstate-li
The Colision detection state resource
ctrlstate = controller state information {motorOn | motorOff}
opmode = operating mode of the controller {manual | auto}
speedratio = speedratio in which the controller is operating
coldetstate = The collision detection states {INIT | TRIGGERED | CONFIRMED | TRIGGERED_ACK}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel"
```

**Notes :** Not supported in bootserver mode

---

## Get Panel Actions

**Chemin :** RobotWare Services › Panel service › Get Panel Actions

URL — /rw/panel

**URL :** `/rw/panel`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
restart
restart the controller
restart-mode
modes are {restart | istart | pstart | bstart}
Required
setlang
Set controller language
lang-code
=[alphanumeric] A valid language code such as
en
,
sv
,
de
etc.
Required
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Set the language

**Chemin :** RobotWare Services › Panel service › Set the language

URL — /rw/panel

**URL :** `/rw/panel`  
**Method :** `POST`

**URL Params :**
```
action=setlang
Required
```

**Data Params :**
```
lang-code = The langauge code e.g.
en
,
sv
,
de
etc
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Set the controller language
curl --digest -u "Default User":robotics -d "lang-code=en" -X POST "http://localhost/rw/panel?action=setlang"
```

**Notes :** Not supported in bootserver mode

---

## Restart the Controller

**Chemin :** RobotWare Services › Panel service › Restart the Controller

URL — /rw/panel

**URL :** `/rw/panel`  
**Method :** `POST`

**URL Params :**
```
action=restart
Required
```

**Data Params :**
```
restart-mode = restart modes are {restart | istart | pstart | bstart}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Restart the controller
curl --digest -u "Default User":robotics -d "restart-mode=restart" -X POST "http://localhost/rw/panel?action=restart"
```

**Notes :** Not supported in bootserver mode

---

## Operations on Controller State Resource

**Chemin :** RobotWare Services › Panel service › Operations on Controller State Resource

---

## Get Controller State

**Chemin :** RobotWare Services › Panel service › Operations on Controller State Resource › Get Controller State

URL — /rw/panel/ctrlstate

**URL :** `/rw/panel/ctrlstate`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
ctrlstate
The controller state. {init | motoron | motoroff | guardstop | emergencystop | emergencystopreset | sysfail}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/ctrlstate"
```

**Notes :** init
: The robot is starting up. It will shift to state motors off when it has started.
motoroff
: The robot is in a standby state where there is no power to the robot's motors. The state has to be shifted to motors on before the robot can move.
motoron
: The robot is ready to move, either by jogging or by running programs.
guardstop
: The robot is stopped because the safety runchain is opened. For instance, a door to the robot's cell might be open.
emergencystop
: The robot is stopped because emergency stop was activated.
emergencystopreset
: The robot is ready to leave emergency stop state. The emergency stop is no longer activated, but the state transition isn't yet confirmed.
sysfail
: The robot is in a system failure state. Restart required.
Not supported in bootserver mode.

---

## Get Controller State Actions

**Chemin :** RobotWare Services › Panel service › Operations on Controller State Resource › Get Controller State Actions

URL — /rw/panel/ctrlstate

**URL :** `/rw/panel/ctrlstate`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set
ctrl-state
=[alphanumeric] can be one of
motoron
or
motoroff
Required
subscribe
for more information refer Subscription Service documentation.
Subscribe on controller state changes.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/ctrlstate?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Set Controller State

**Chemin :** RobotWare Services › Panel service › Operations on Controller State Resource › Set Controller State

URL — /rw/panel/ctrlstate

**URL :** `/rw/panel/ctrlstate`  
**Method :** `POST`

**URL Params :**
```
action=setctrlstate
Required
```

**Data Params :**
```
ctrl-state = The controller state {motoron | motoroff}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
Set controller state
curl --digest -u "Default User":robotics -d "ctrl-state=motoron" -X POST "http://localhost/rw/panel/ctrlstate?action=setctrlstate"
```

**Notes :** Not supported in bootserver mode.

---

## Subscribe Controller state

**Chemin :** RobotWare Services › Panel service › Operations on Controller State Resource › Subscribe Controller state

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/panel/ctrlstate')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
pnl-ctrlstate-ev
ctrlstate
Controller state {init | motoron | motoroff | guardstop | emergencystop | emergencystopreset | sysfail}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on controller state changes
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/ctrlstate&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/ctrlstate&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** init
: The robot is starting up. It will shift to state motors off when it has started.
motoroff
: The robot is in a standby state where there is no power to the robot's motors. The state has to be shifted to motors on before the robot can move.
motoron
: The robot is ready to move, either by jogging or by running programs.
guardstop
: The robot is stopped because the safety runchain is opened. For instance, a door to the robot's cell might be open.
emergencystop
: The robot is stopped because emergency stop was activated.
emergencystopreset
: The robot is ready to leave emergency stop state. The emergency stop is no longer activated, but the state transition isn't yet confirmed.
sysfail
: The robot is in a system failure state. Restart required.
Not supported in bootserver mode

---

## Operations on Operation Mode Resource

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource

---

## Get Operation Mode

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource › Get Operation Mode

URL — /rw/panel/opmode

**URL :** `/rw/panel/opmode`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
opmode
The operation mode {INIT | AUTO_CH | MANF_CH | MANR | MANF | AUTO | UNDEF}
INIT
: State init
AUTO_CH
: State change request for automatic mode
MANF_CH
: State change request for manual mode & full speed
MANR
: State manual mode & reduced speed
MANF
: State manual mode & full speed
AUTO
: State automatic mode
UNDEF
: Undefined
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/opmode"
```

**Notes :** Not supported in bootserver mode

---

## Get Operation  Mode Actions

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource › Get Operation  Mode Actions

URL — /rw/panel/opmode

**URL :** `/rw/panel/opmode`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set
set the opmode as { Lock | unlock}
subscribe
for more information refer Subscription Service documentation.
Subscribe on controller operation mode.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/opmode?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe Operation Mode

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource › Subscribe Operation Mode

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/panel/opmode')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
pnl-opmode-ev
opmode
Controller Operation Mode {INIT | AUTO_CH | MANF_CH | MANR | MANF | AUTO | UNDEF}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on controller state changes
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/opmode&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/opmode&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Acknowledgement for Operation Mode

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource › Acknowledgement for Operation Mode

URL — /rw/panel/opmode

**URL :** `/rw/panel/opmode`  
**Method :** `POST`

**URL Params :**
```
action=acknowledge
Required
```

**Data Params :**
```
opmode={auto | manf | coldet}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
UNSUPPORTED_MEDIA (415)
FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "opmode=auto" -X POST "http://localhost/rw/panel/opmode?action=acknowledge"
```

**Notes :** Client should have Local Client previliges to execute the functionality.
Auto acknowledgement option should be deactivated.
Not supported in bootserver mode.

---

## Get Operation Mode Lock Status

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource › Get Operation Mode Lock Status

URL — /rw/panel/opmode

**URL :** `/rw/panel/opmode`  
**Method :** `GET`

**URL Params :**
```
resource=lock-state
Required
```

**Data Params :**
```
None
```

**Resources :**
```
lock-state:
The Mode selector lock state gives { error | unlocked | locked | permlocked | pendpermlocked}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/opmode?resource=lock-state"
```

**Notes :** Not supported in bootserver mode

---

## Lock operation mode selection.

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource › Lock operation mode selection.

URL — /rw/panel/opmode

**URL :** `/rw/panel/opmode`  
**Method :** `POST`

**URL Params :**
```
action=lock
Required
See
Common URL parameters
```

**Data Params :**
```
pin=<4-digit-pin>
Required
permanent=<1|0>
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "pin=1234&permanent=0" -X POST "http://localhost/rw/panel/opmode?action=lock"
```

**Notes :** Not supported in bootserver mode.
UAS_GRANT "Lock saftey controller config" is needed to lock/unlock.
For permenant lock/unlock "Key-less mode selector" UAS_GRANT is needed.

---

## Unlock operation mode selection.

**Chemin :** RobotWare Services › Panel service › Operations on Operation Mode Resource › Unlock operation mode selection.

URL — /rw/panel/opmode

**URL :** `/rw/panel/opmode`  
**Method :** `POST`

**URL Params :**
```
action=unlock
Required
See
Common URL parameters
```

**Data Params :**
```
pin=<4-digit-pin>
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "pin=1234" -X POST "http://localhost/rw/panel/opmode?action=unlock"
```

**Notes :** Not supported in bootserver mode.
UAS_GRANT "Lock saftey controller config" is needed to lock/unlock.
For permenant lock/unlock "Key-less mode selector" UAS_GRANT is needed.

---

## Operations on Speed Ratio Resource

**Chemin :** RobotWare Services › Panel service › Operations on Speed Ratio Resource

---

## Get Speed Ratio

**Chemin :** RobotWare Services › Panel service › Operations on Speed Ratio Resource › Get Speed Ratio

URL — /rw/panel/speedratio

**URL :** `/rw/panel/speedratio`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
speedratio
The speed ratio value. {0-100}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/speedratio"
```

**Notes :** Not supported in bootserver mode

---

## Get Speed Ratio Actions

**Chemin :** RobotWare Services › Panel service › Operations on Speed Ratio Resource › Get Speed Ratio Actions

URL — /rw/panel/speedratio

**URL :** `/rw/panel/speedratio`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
set-speed-ratio
Set the speed ratio
speed-ratio
=[numeric]
Required
, can be a value between 0 and 100
subscribe
, for more information refer to Subscription service documentation
Subscribe on speed ratio changes.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/speedratio?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Set Speed Ratio

**Chemin :** RobotWare Services › Panel service › Operations on Speed Ratio Resource › Set Speed Ratio

URL — /rw/panel/speedratio

**URL :** `/rw/panel/speedratio`  
**Method :** `POST`

**URL Params :**
```
action=setspeedratio
Required
```

**Data Params :**
```
speed-ratio = The speed ratio value between 0 and 100
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST (400), UNSUPPORTED_MEDIA (415), FORBIDDEN (403)
See
Robot controller return codes

**Sample Call :**
```bash
Set speed ratio
curl --digest -u "Default User":robotics -d "speed-ratio=60" -X POST "http://localhost/rw/panel/speedratio?action=setspeedratio"
```

**Notes :** Only supported in auto mode.
Not supported in bootserver mode

---

## Subscribe Speed Ratio

**Chemin :** RobotWare Services › Panel service › Operations on Speed Ratio Resource › Subscribe Speed Ratio

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/panel/speedratio')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Resources :**
```
pnl-speedratio-ev
speedratio
The Speed Ratio { 0 - 100 }
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on controller state changes
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/speedratio&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/speedratio&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Operations on Collision Detection State

**Chemin :** RobotWare Services › Panel service › Operations on Collision Detection State

---

## Get Collision Detection State

**Chemin :** RobotWare Services › Panel service › Operations on Collision Detection State › Get Collision Detection State

URL — /rw/panel/coldetstate

**URL :** `/rw/panel/coldetstate`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
coldetstate
The collision detection states {INIT | TRIGGERED | CONFIRMED | TRIGGERED_ACK}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/coldetstate"
```

**Notes :** Not supported in bootserver mode

---

## Get Collision Detection State Actions

**Chemin :** RobotWare Services › Panel service › Operations on Collision Detection State › Get Collision Detection State Actions

URL — /rw/panel/coldetstate

**URL :** `/rw/panel/coldetstate`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
subscribe
for more information refer Subscription Service documentation.
Subscribe on collision detection state changes.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/panel/coldetstate?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on Collision Detection State

**Chemin :** RobotWare Services › Panel service › Operations on Collision Detection State › Subscribe on Collision Detection State

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
<identifier> = An identifier
Required
resources
= The subscription resource URI (The URI here is: '/rw/panel/coldetstate')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on controller state changes
only low priority subscription(1-p=0) and medium priority subscription(1-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/coldetstate&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/panel/coldetstate&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## RAPID Service

**Chemin :** RobotWare Services › RAPID Service

---

## Get RAPID system resources

**Chemin :** RobotWare Services › RAPID Service › Get RAPID system resources

URL — /rw/rapid

**URL :** `/rw/rapid`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
rap-tasks-li
Rapid tasks resource list item
rap-symbols-li
Rapid symbols list item
rap-execution-li
Rapid execution list item
rap-uiinstr-li
Rapid UI instruction list item
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Sample Call :**
```bash
curl –digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid
"
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID execution

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution

---

## Get RAPID Execution state

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Get RAPID Execution state

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `GET`

**URL Params :**
```
continue-on-err={1|0}
Optional
Default value is 0. In case input is 1, the API continues execution even if any error occurs in between.
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
rap-execution
Rapid execution resource
ctrlexecstate
Rapid execution state {running | stopped}
cycle
Current run mode { forever | asis | once | oncedone }
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/execution"
```

**Notes :** Not supported in bootserver mode.
Use /rw/rapid/execution;ctrlexecstate to filter ctrlexecstate value.

---

## Get RAPID Execution actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Get RAPID Execution actions

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Actions :**
```
rap-execution
start
Start RAPID Execution
stop
Stop RAPID Execution
startprodentry
Start RAPID Execution from production entry
resetpp
Reset RAPID program pointer to main
setcycle
Set number of execution cycles
subscribe
Subscribe RAPID Execution
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/rapid/execution?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Start RAPID Execution

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Start RAPID Execution

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `POST`

**URL Params :**
```
action=start
Required
See
Common URL parameters
```

**Data Params :**
```
regain={continue | regain | clear}
Required
execmode={continue | stepin | stepover | stepout | stepback | steplast | stepmotion}
Required
cycle={forever | asis | once}
Required
condition={none | callchain}
Required
stopatbp={disabled | enabled} (stop at breakpoint)
Required
alltaskbytsp={true | false}
Required
data params form data see
Get RAPID Execution actions
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "regain=continue&execmode=continue&cycle=forever&condition=none&stopatbp=disabled&alltaskbytsp=false" "http://localhost/rw/rapid/execution?action=start"
```

**Notes :** Not supported in bootserver mode.

---

## Stop RAPID Execution

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Stop RAPID Execution

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `POST`

**URL Params :**
```
action=stop
Required
```

**Data Params :**
```
stopmode={cycle | instr | stop | qstop} (default: stop)
usetsp={normal | alltsk} (default: normal)
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/execution?action=stop"
```

**Notes :** Not supported in bootserver mode

---

## Start RAPID Execution from production entry

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Start RAPID Execution from production entry

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `POST`

**URL Params :**
```
action=startprodentry
Required
```

**Data Params :**
```
None*
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/execution?action=startprodentry"
```

**Notes :** Not supported in bootserver mode

---

## Reset RAPID program pointer to main

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Reset RAPID program pointer to main

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `POST`

**URL Params :**
```
action=resetpp
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/execution?action=resetpp"
```

**Notes :** Not supported in bootserver mode

---

## Set number of execution cycles

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Set number of execution cycles

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `POST`

**URL Params :**
```
action=setcycle
Required
```

**Data Params :**
```
cycle= {once | forever}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "cycle=once" -X POST "http://localhost/rw/rapid/execution?action=setcycle"
```

**Notes :** Not supported in bootserver mode.
Mastership is required to set cycle.

---

## Subscribe RAPID Execution

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Subscribe RAPID Execution

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
resources={identifier}
*<identifier>*= The subscription resource URI
*<identifier>-p*= The priority associated with the subscription resource.
Subscription parameters
Get RAPID Execution actions
```

**Resources :**
```
rap-ctrlexecstate-ev
Controller rapid execution event resource
ctrlexecstate
Controller rapid execution state {running | stopped}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID execution state
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/execution;ctrlexecstate&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/execution;ctrlexecstate&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe RAPID Execution Cycle

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Subscribe RAPID Execution Cycle

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources={identifier}
*<identifier>*= The subscription resource URI
*<identifier>-p*= The priority associated with the subscription resource.
Subscription parameters
Get RAPID Execution actions
```

**Resources :**
```
rap-execcycle-ev
Controller rapid execution cycle event resource
rapidexeccycle
Controller rapid execution cycle {PGMRUN_CYCLE_CONTINUOUS | PGMRUN_CYCLE_SINGLE}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID execution cycle
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/execution;rapidexeccycle&1-p=0" "http://localhost/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/execution;rapidexeccycle&1-p=1" "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on Hold to Run

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Subscribe on Hold to Run

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/execution;hdtrun')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-hdtr-ev
hdtr-State
{HdTREvent WaitEntered|HdTREvent WaitLeft}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID hold to run
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/execution;hdtrun&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/execution;hdtrun&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Set Hold to Run Cmd

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID execution › Set Hold to Run Cmd

URL — /rw/rapid/execution

**URL :** `/rw/rapid/execution`  
**Method :** `POST`

**URL Params :**
```
action=holdtorun-state
Required
```

**Data Params :**
```
state={press | held | release}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400),FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST -d "state={press | held | release}" "http://localhost/rw/rapid/execution?action=holdtorun-state"
```

**Notes :** -Not supported in bootserver mode
-Supported in VC only
-Login as Local Client
-The Hold-To-Run control prevents RAPID-program execution to start until the holdtorun state is changed to Press.
-In the state Pressed the client must poll the Hold-To-Run control every 2 second, otherwise the program execution will stop. This is done by setting the holdtorun state to Held.
-If the client want's to stop the program execution immediately it must change the state to Release.
-Rapid program should run in motors on state.
-operation mode should be Manual(Reduced Speed) or Manual Full Speed.

---

## Operations on RAPID modules

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules

---

## Get RAPID modules action

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Get RAPID modules action

URL — /rw/rapid/modules

**URL :** `/rw/rapid/modules`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/rapid/modules?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Get RAPID modules

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Get RAPID modules

URL — /rw/rapid/modules

**URL :** `/rw/rapid/modules`  
**Method :** `GET`

**URL Params :**
```
task={task name}
Required
Name of task from which modules shall be listed
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-module-info-li
Rapid tasks resource list item
name
Module name
type
Module type {ProgMod | SysMod}
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/modules?task=T_ROB1"
```

**Notes :** Not supported in bootserver mode

---

## Get Mod Possible All

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Get Mod Possible All

URL — /rw/rapid/modules

**URL :** `/rw/rapid/modules`  
**Method :** `GET`

**URL Params :**
```
resource=mod-possible-all
Required
```

**Data Params :**
```
None*
```

**Resources :**
```
module-name
Rapid module name
task-name
Task name
start-row
Start Row
start-col
Start Col
end-row
End Row
end-col
End Col
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/modules?resource=mod-possible-all"
```

**Notes :** Not supported in bootserver mode

---

## Set Modify All Positions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Set Modify All Positions

URL — /rw/rapid/modules

**URL :** `/rw/rapid/modules`  
**Method :** `POST`

**URL Params :**
```
action=modify-all-position
Required
```

**Data Params :**
```
checklimit={true | false}
Required
checkdeactaxes={true | false}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST -d "checklimit=false&checkdeactaxes=false" "http://localhost/rw/rapid/modules?action=modify-all-position"
```

**Notes :** User needs to be local client and mastership is also required
Not supported in bootserver mode

---

## Operations on rapid module

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module

---

## Get a specified range of text

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get a specified range of text

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
task
= {task}
startrow
= {start row}
startcol
= {start column}
endrow
= {end row}
endcol
= {end column}
Data Params
None
```

**Resources :**
```
rap-mod-text
Provides RAPID module text
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/mymodule?task=T_ROB1&startrow=1&startcol=1&endrow=20&endcol=-1"
```

**Notes :** Not supported in bootserver mode

---

## Get rapid module actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get rapid module actions

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/modules/MainModule?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Save rapid module

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Save rapid module

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `POST`

**URL Params :**
```
task={Task Name}
Required
action=save
Required
, form data see
Get rapid module actions
```

**Data Params :**
```
name={module_name} Saved module will be with .mod extension.
Required
path={file_path} Real path or RobotWare environment variables such as $HOME, $TEMP can be used in the file path.
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=MainModule&path=C:\Users\mymod" -X POST "http://localhost/rw/rapid/modules/MainModule?task=T_ROB1&action=save"
```

**Notes :** Not supported in bootserver mode

---

## Set Text Range

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Set Text Range

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `POST`

**URL Params :**
```
action=set-text-range
Required
```

**Data Params :**
```
task={Task Name}
Required
replace-mode={After | Before | Replace}
Required
query-mode={Force | Try} Try mode required program pointer
Required
startrow = {Start Row Number}
Required
startcol = {Start Column Number}
Required
endrow = {End Row Number}
Required
endcol = {End Column Number}
Required
text={Input Text}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "task=T_ROB1&replace-mode=After&query-mode=Force&startrow=8&startcol=8&endrow=8&endcol=15&text=SampleTest" -X POST "http://localhost/rw/rapid/modules/MainModule?action=set-text-range"
```

**Notes :** Mastership is Required
Not supported in bootserver mode

---

## Set Module Text

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Set Module Text

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `POST`

**URL Params :**
```
task={Task Name}
Required
action=set-module-text
Required
```

**Data Params :**
```
text={Input Text}
Required
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400),NOT_FOUND(404), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST -d "text=SampleTest" -X POST "http://localhost/rw/rapid/modules/MainModule?task=T_ROB1&action=set-module-text"
```

**Notes :** Not supported in bootserver mode

---

## Get RAPID module attributes

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get RAPID module attributes

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
task=T_ROB1
Required
continue-on-err={1|0}
Optional
Default value is 0. In case input is 1, the API continues execution even if any error occurs in between.
```

**Data Params :**
```
None
```

**Resources :**
```
rap-module
Provides RAPID module attributes
modname
Name of the module.
filename
Name of the module file.
attribute
{sysmod|encode|noview|nostepin|viewonly|readonly} Module attributes.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/mymodule?task=T_ROB1"
```

**Notes :** Not supported in bootserver mode

---

## Get change count

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get change count

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=change-count
Required
task={task_name}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
rap-module-changecount
count changecount.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** Bad Request(400), FORBIDDEN(403), NOT_FOUND(404), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule?resource=change-count&task=T_ROB1"
```

---

## Get RulesInstr

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get RulesInstr

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=rules-instr
Required
task={task_name}
Required
name={datatype_name | instruction_name}
Required
data-type=true | false
line={line_num}
col={column_num}
parnum={parnum_value}
altnum={altnum_value}
```

**Data Params :**
```
None
```

**Resources :**
```
rap-module-rulesinstr
rapid module suggested templete for data type or instruction.
arg-num
Parameter number.
required
TRUE for mandatory argument and FALSE for optional argument.
arg-name
Parameter name
dec-data
True if symbol declarataion needed
arg-symbol
Argument symbol name or empty if literal
data-value
Symbol initial value
data-type
Symbol datatype
obj-type
Object type like CONST, VAR and PERS.
local
Declared locally if TRUE.
ndim
Number of dimensions
num-args
Number of arguments that are retrieved as part of the response.
mark
Index value where it is started retrieving.
last
All arguments are read if value is 1.
data-type(url parameter)
Name parameter value is considered as data type when data-type value is true and default value is false.
parnum(url parameter)
Formal parameter number to override rules
altnum(url parameter)
Alternative parameter number to override rules and it can be used along with parnum to get optional parameters.
col(url parameter)
column number
line(url parameter)
row number.
name(url parameter)
data type or instruction name.
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule?resource=rules-instr&task=T_ROB1&name=movej"
```

---

## Get module possible attributes

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get module possible attributes

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
task=T_ROB1
Required
attribute={attribute-combination}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
rap-mod-text
Provides RAPID module text
attribute
Rapid module attribtes(System module, No step in module, Read only module)
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/mymodule?task=T_ROB1&attribute=readonly&attribute=nostepin"
```

**Notes :** -Not supported in bootserver mode
-URL param "attribute" can be provided multiple times

---

## Get Search Text

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get Search Text

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
task={Task Name}
Required
startrow={Start Row Number}
Required
startcol={Start Column Number}
Required
text={search text}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
rap-text-position
Row- Row number of Text.
Column- Column number of Text.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403), NOT_FOUND(404), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule?task=T_ROB1&startrow=1&startcol=1&text=main"
```

**Notes :** Not supported in bootserver mode.
If the text is not found,the row and column values will be zero.

---

## Get Rapid Object

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get Rapid Object

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
task
= {task}
Required
startrow
= {start row}
Required
startcol
= {start column}
Required
destination
={Inner|Outer|Outer2|Before|After|Statement|InnerStatement}
Optional
```

**Data Params :**
```
None
```

**Resources :**
```
rap-object
start-row
Starting position of the row.
start-column
Starting position of the column.
end-row
Ending position of the row.
end-column
Ending position of the column.
type
Type of the object.
list-num
List element number.
list-len
Number of list elements.
data-type-id
Symbol name.
data-type-instance
Symbol name instance number.
expression-type
Expression type.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST (400), FORBIDDEN(403), NOT_FOUND(404), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/BASE?task=T_ROB1&startrow=3&startcol=2&destination=Inner"
```

**Notes :** Not supported in bootserver mode

---

## Set SyncPers

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Set SyncPers

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `POST`

**URL Params :**
```
action=set-syncpers
Required
task={task_name}
Required
```

**Data Params :**
```
None
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** BAD_REQUEST(400)
FORBIDDEN(403), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/modules/MainModule?action=set-syncpers&task=T_ROB1"
```

---

## Set Modify Position

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Set Modify Position

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `POST`

**URL Params :**
```
action=modify-position
Required
task={Task Name}
Required
```

**Data Params :**
```
startrow={start Row Number}
Required
startcol={start Col Number}
Required
endrow={End Row Number}
Required
endcol={End Col Number}
Required
checklimit={false | true}
Required
checkdeactaxes={false | true}
Required
allowdeact={false | true}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** Bad Request(400),
FORBIDDEN(403),
NOT_FOUND(404) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST -d "startrow=3&startcol=9&endrow=3&endcol=102&checklimit=false&checkdeactaxes=false&allowdeact=false" "http://localhost:2222/rw/rapid/modules/MainModule?action=modify-position&task=T_ROB1"
```

---

## Get Module Extension

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get Module Extension

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=module-extension
Required
task={task_name}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
num-of-lines:
Number of rows in RAPID module
max-num-of-col:
Maximum number of cols in RAPID module
count:
Change Count
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule?resource=module-extension&task=T_ROB1"
```

---

## Get Mod Possible

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get Mod Possible

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=mod-possible
Required
task={task_name}
Required
startrow = {Start Row Number}
Required
startcol = {Start Column Number}
Required
endrow = {End Row Number}
Required
endcol = {End Column Number}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
no_lines_modifiable
Number of modifiable motion instructions
start_row
Start Row
start_col
Start Col
end_row
End Row
end_col
End Col
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule?resource=mod-possible&task=T_ROB1&startrow=19&startcol=1&endrow=21&endcol=1"
```

---

## Get Object Child

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get Object Child

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=object-child
Required
task={task_name}
Required
startline={startline}
Required
startcolumn={startcolumn}
Required
endline={endline}
Required
endcolumn={endcolumn}
Required
startline & startcolumn: refers to the start of the object
endline & endcolumn: referes to the end of object extent
choose the entire extent of the object, to obtain the details(children) of the object
```

**Data Params :**
```
None
```

**Resources :**
```
object-type:
type of the object for which extent details are obtained.
extent details are: startline(beg-line), startcolumn(beg-col), endline(end-line), endcolumn(end-col)
Note
output varies with the object type under consideration
object type examples : module, procedure declaration, data declaration, function declaration etc.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost:4444/rw/rapid/modules/base?resource=object-child&task=T_ROB1&startline=1&startcolumn=1&endline=16&endcolumn=9"
```

---

## Get SyncPers Status

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get SyncPers Status

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=syncper-status
Required
task={task_name}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
syncperstatus:
status from Persistent variable {1 - TRUE|0 - FALSE}
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/base?resource=syncper-status&task=T_ROB1"
```

---

## Get Module Text

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get Module Text

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=module-text
Required
task={task_name}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
change-count:
System configuration change count number
module-text:
RAPID program for a given task
module-length:
maximum length of module
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule?resource=module-text&task=T_ROB1"
```

---

## Get Symbol Information

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Get Symbol Information

URL — /rw/rapid/modules/{module}

**URL :** `/rw/rapid/modules/{module}`  
**Method :** `GET`

**URL Params :**
```
resource=module-symbol
Required
task={task_name}
Required
row={row number}
Required
col={col number}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
version:
version number
symbolname:
RAPID symbol name
block_url:
RAPID symbol URL
sysmbol_type:
RAPID symbol Type
linked:
TRUE if definition is complete
local:
FALSE if global module constant
typurl:
URL to type symbol
dattyp:
Underlying data type
ndim:
Number of array dimensions
storage:
Symbol declaration storage
heap:
TRUE if heap allocated (always TRUE)
refcount:
Reference count
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule?resource=module-symbol&task=T_ROB1&row=5&col=9"
```

---

## Operations on RAPID Routine

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Operations on RAPID Routine

---

## Get Routine information

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Operations on RAPID Routine › Get Routine information

URL — /rw/rapid/modules/{module}/routine

**URL :** `/rw/rapid/modules/{module}/routine`  
**Method :** `GET`

**URL Params :**
```
task={task}
Required
row={row}
Required
column={column}
Required
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-routine-prop
name
The name of the symbol. NULL if not retreived
symtyp
Type pf symbol {prc | fun | trp}
named
True if symbol is named.
local
{true|false}, FALSE if global module procedure
npar
Number of routine parameters, -1 if parameter list not linked
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** HTTP_BAD_REQUEST(400),FORBIDDEN(403), NOT_FOUND(404),see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule/routine?task=T_ROB1&row=10&column=9"
```

**Notes :** Not supported in bootserver mode

---

## Get Routineargs information

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID modules › Operations on rapid module › Operations on RAPID Routine › Get Routineargs information

URL — /rw/rapid/modules/{module}/routine

**URL :** `/rw/rapid/modules/{module}/routine`  
**Method :** `GET`

**URL Params :**
```
resource=routine-args
Required
mark={mark} (index of the element)
limit={numberofelements}
task={task}
Required
row={row}
Required
column={column}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
next
Link to next page (Will be absent if there is no next page)
rap-routine-args
RAPID routine argument list item
param-no
Param number
alternate-arg
Alternate argument number
start-row
Starting row of argument
start-col
Starting column of argument
end-row
Ending row of argument
end-col
Ending column of argument
rap-objtype
Rap object type
data-type
Argument data type
list-num
List number of argument
list-len
Total number of arguments
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400),FORBIDDEN(403), NOT_FOUND(404), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/modules/MainModule/routine?resource=routine-args&mark=3&limit=3&task=T_ROB1&row=4&column=9"
```

**Notes :** Routineargs will show a list of arguments based on the mark and limit.
Default value of mark is 0.
Absence of next link indicates last page.
You will get routine argument information only on lines having proceure call.
Not supported in bootserver mode.

---

## Operations on RAPID symbols properties

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbols properties

---

## Get RAPID symbols resources

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbols properties › Get RAPID symbols resources

URL — /rw/rapid/symbols

**URL :** `/rw/rapid/symbols`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
None*
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/symbols
"
```

**Notes :** Not supported in bootserver mode

---

## Get rapid symbols actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbols properties › Get rapid symbols actions

URL — /rw/rapid/symbols

**URL :** `/rw/rapid/symbols`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
search-symbols
view
Search for symbols in {block | scope | stack}
posl
Line position in module
posc
Column position in module (if posl and posc are both 0 is the blockurl used instead)
blockurl
Relative URL describing the block where the search should start. A relative url never has a leading '/'. The global block, with shared symbols, has the url 'RAPID'.
stack
The stackframe to search when searching in stack. Current stackframe is always 1.
recursive
True if the search should be recursive.
onlyused
True if only used symbols should be returned.
skipshared
True if shared symbols should be skipped
regexp
dattyp
Search for symbols of 'data-type'
symtyp
Search for symbol of symbol type:
atm Atomic symbol. For example, the predefined symbol 'num' has type Atomic.
rec Record type. For example, the predefined symbol 'RobTarget' has type Record.
ali Alias type.
rcp Record component.
con Constant. For example, 'myvar' in the declaration 'CONST num myvar = 1;' has type Constant.
var Variable. For example, 'myvar' in the declaration 'VAR num myvar;' has type Variable.
per Persistent. For example, 'myvar' in the declaration 'PERS num myvar=1;' has type Persistent.
par Parameter
lab Label
for For statement
fun Function
prc Procedure
trp Trap
mod Module
tsk Task
any Any type
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/symbols?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Search RAPID symbols

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbols properties › Search RAPID symbols

URL — /rw/rapid/symbols

**URL :** `/rw/rapid/symbols`  
**Method :** `POST`

**URL Params :**
```
action=search-symbol
Required
```

**Data Params :**
```
At least one data parameter should be provided.
view = {block | scope | stack }. For both scope and stack you must use blockurl with task, for stack even program pointer should be set.
vartyp = {udef | rw | ro | loop | any}.Variable type to be searched.
blockurl = {string}.Relative URL describing the block where the search should start.
recursive = {TRUE | FALSE}.True if search should be recursive otherwise false.
posl = {position row}.Line position in module.
posc = {position col}.Column position in module (if posl and posc are both 0 is the blockurl used instead).
stack = {integer}.stackframe to search when searching in stack.
onlyused = {TRUE|FALSE}.True if only used symbols should be returned.
skipshared = {TRUE|FALSE}.True when shared symbols should be skipped,otherwise False.
regexp = {regular expression}
symtyp = { atm | rec | ali | rcp | con | var | per | par | lab | for | fun | prc | trp | mod | tsk | any | udef}.Type of Symbol to be searched.
atm Atomic type
rec Record type
ali Alias type
rcp Record component
con Constant
var Variable
per Persistent
par Parameter
lab Label
for For statement
fun Function
prc Procedure
trp Trap
mod Module
tsk Task
any any of the above symbol type
dattyp = {string}.,Datatype which has to be filtered.
```

**Resources :**
```
rap-sympropvar-li
Rapid-Symbol resource
symburl
the name of the symbol. NULL if not retreived
name
the name of the symbol. NULL if not retreived
symtyp
the symbol properties. NULL if not retreived
named
true if symbol is named. Undefined if the symbol
dattyp
underlying type
ndim
number of array dimensions
dim
array dimensions
local
FALSE if global module constant
rdonly
TRUE if variable is readonly
taskvar
TRUE if var is global within task
typurl
URL to type symbol
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "view=block&vartyp=any&blockurl=RAPID/T_ROB1&symtyp=var&recursive=true&dattyp=num&skipshared=TRUE&onlyused=TRUE&stack=0&posl=0&posc=0" "http://127.0.0.1/rw/rapid/symbols?action=search-symbols"
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID symbol object

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbols properties › Operations on RAPID symbol object

---

## Get Object Extension List

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbols properties › Operations on RAPID symbol object › Get Object Extension List

URL — /rw/rapid/symbols/{symbol URL}

**URL :** `/rw/rapid/symbols/{symbol URL}`  
**Method :** `GET`

**URL Params :**
```
info=object-list-ext
type={Statements | BackwardStmts | ErrorStmts | UndoStmts | TypeDecls | DataDecls | ParDecls | RtnDecls | Attribs}
See
Common URL parameters
Option definition
Statements = statements
BackwardStmts = Backward Statements
UndoStmts = Undo Statements
TypeDecls = Type Declarations
DataDecls = Data Declarations
ParDecls = Parameter Declarations
RtnDecls = Routine Declarations
Attribs = Attributes
```

**Data Params :**
```
None*
```

**Resources :**
```
ext-begin-line
Begin line number of the object extension list
ext-begin-column
Begin column number of the object extension list
ext-end-line
End line number of the object extension list
ext-end-column
End column number of the object extension list
ext-first-begin-line
Begin line number of the first object in the list
ext-first-begin-column
Begin column number of the first object in the list
ext-first-end-line
End line number of the first object in the list
ext-first-end-column
End column number of the first object in the list
ext-last-begin-line
Begin line number of the last object in the list
ext-last-begin-column
Begin column number of the last object in the list
ext-last-end-line
End line number of the last object in the list
ext-last-end-column
End column number of the last object in the list
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/symbols/RAPID/T_ROB1/mainmodule?info=object-list-ext&type=DataDecls
"
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID symbol

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol

---

## Operations on RAPID symbol properties

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol properties

---

## Get RAPID symbol properties

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol properties › Get RAPID symbol properties

URL — /rw/rapid/symbol/properties/{symbolurl}

**URL :** `/rw/rapid/symbol/properties/{symbolurl}`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Resources :**
```
rap-sympropvar
symburl
Symbol URL
symtyp
Symbol type {udef | atm | rec | ali | rcp | con | var | per | par | lab | for | fun | prc | trp | mod | tsk | any}
named
{True | False}
dattyp
Data type
ndim
Number of array dimensions
dim
Array dimensions
heap
{True | False} TRUE if heap allocated
linked
{True | False} TRUE if definition is complete
local
{True | False} FALSE if global module persistent
ro
{True | False} TRUE if persistent is readonly
taskvar
{True | False} TRUE if var is global within task
storage
Symbol declaration storage
typurl
URL to type symbol
```

**Success :** HTTP_OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Common return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics
http://192.168.8.105/rw/rapid/symbol/properties/RAPID/T_ROB1/user/reg1
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID symbol data

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol data

---

## Get rapid symbol data

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol data › Get rapid symbol data

URL — /rw/rapid/symbol/data/{symbolurl}

**URL :** `/rw/rapid/symbol/data/{symbolurl}`  
**Method :** `GET`

**URL Params :**
```
value=raw* Returns a non stringify json value.
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-data
rapid data
rap-data-decl-pos
rapid data decleration position
begin-row
begin row number
begin-coloumn
begin column number
end-row
end row number
end-coloumn
end column number
rap-data-initval-pos
rapid data initial value position
begin-row
begin row number
begin-coloumn
begin column number
end-row
end row number
end-coloumn
end column number
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics
http://localhost/rw/rapid/symbol/data/RAPID/T_ROB1/user/reg1
```

**Notes :** Not supported in bootserver mode

---

## Get rapid symbol data actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol data › Get rapid symbol data actions

URL — /rw/rapid/symbols/{symbolurl}

**URL :** `/rw/rapid/symbols/{symbolurl}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
sub-value
sub value
priority
selected priority
selected
selected value
```

**Actions :**
```
set
Update RAPID data
Update rapid variable current value
subscribe
It is possible to subscribe on persistent RAPID variables
Subscribe on RAPID persistent variable
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400) see
HTTP Status codes
Robot controller errors, see common_return_code

**Sample Call :**
```bash
curl --digest -u "Default User":robotics
http://localhost/rw/rapid/symbol/data/RAPID/T_ROB1/user/reg1?action=show
```

**Notes :** Not supported in bootserver mode

---

## Update rapid variable current value

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol data › Update rapid variable current value

URL — /rw/rapid/symbol/data/{symbolurl}

**URL :** `/rw/rapid/symbol/data/{symbolurl}`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
See
Common URL parameters
```

**Data Params :**
```
value = {value_num}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** FORBIDDEN(403) BAD REQUEST(400) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Update a num:
curl --digest -u "Default User":robotics -d "value=10" "http://localhost/rw/rapid/symbol/data/RAPID/T_ROB1/user/reg1?action=set"
Update a string: curl –digest -u "Default User":robotics -d "value=\"10"" "
http://localhost/rw/rapid/symbol/data/RAPID/T_ROB1/MyMod/SStr?action=set
"
```

**Notes :** Not supported in bootserver mode
Client needs RAPID mastership in AUTO mode. Client needs RMMP Privilege and RAPID mastership in MANUAL mode.

---

## Validate rapid variable

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol data › Validate rapid variable

URL — /rw/rapid/symbol/data

**URL :** `/rw/rapid/symbol/data`  
**Method :** `POST`

**URL Params :**
```
action=validate
Required
See
Common URL parameters
```

**Data Params :**
```
task
Task name
Required
value
Value
Required
datatype
Data type
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415), BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "task=T_ROB1&value=[TRUE,[[0,0,0],[-1,0,0,0]],[1,[0,0,-1],[1,0,0,0],0,0,0]]&datatype=tooldata" "http://localhost/rw/rapid/symbol/data?action=validate"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on RAPID persistent variable

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol data › Subscribe on RAPID persistent variable

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None*
```

**Data Params :**
```
resources
= {resource_value}
Get rapid symbol data actions
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/symbol/data/RAPID/T_ROB1/uimsg/PNum2;value')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-value-ev
rapid value event resource
```

**Success :** CREATED(201), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID persistent value. The resource url to subscribe on shall be on the form /rw/rapid/symbol/data/{symbolurl};value.
It is possible to possible to subscribe with any subscription priority (i.e High, Medium, Low priority) for RAPID persistent variables value.
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/symbol/data/RAPID/T_ROB1/uimsg/PNum2;value&1-p=2" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/symbol/data/RAPID/T_ROB1/uimsg/PNum1;value&1-p=1" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/symbol/data/RAPID/T_ROB1/uimsg/PNum2;value&1-p=0" "http://127.0.0.1/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Update rapid variable Initial Value

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID symbol › Operations on RAPID symbol data › Update rapid variable Initial Value

URL — /rw/rapid/symbol/data/{symbolurl}

**URL :** `/rw/rapid/symbol/data/{symbolurl}`  
**Method :** `POST`

**URL Params :**
```
action=setInitValue
Required
See
Common URL parameters
```

**Data Params :**
```
value={some_value} form data see
Get rapid symbol data actions
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Update a num:
curl --digest -u "Default User":robotics -d value=10 "http://localhost/rw/rapid/symbol/data/RAPID/T_ROB1/user/reg1?action=setInitValue"
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID tasks

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks

---

## Get RAPID tasks

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Get RAPID tasks

URL — /rw/rapid/tasks

**URL :** `/rw/rapid/tasks`  
**Method :** `GET`

**URL Params :**
```
continue-on-err={1|0}
Optional
Default value is 0. In case input is 1, the API continues execution even if any error occurs in between.
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-task-li
RAPID tasks resource list item
name
Task name
type
Task type
taskstate
task state can be empty, initiated,linked or loaded.
excstate
task execution state can be ready,stopped,started or uninitialized.
active
task active state.
motiontask
motion state of task.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks"
```

**Notes :** Not supported in bootserver mode

---

## Get rapid Tasks actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Get rapid Tasks actions

URL — /rw/rapid/tasks

**URL :** `/rw/rapid/tasks`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/tasks?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Start RAPID Spy Logging

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Start RAPID Spy Logging

URL — /rw/rapid/tasks

**URL :** `/rw/rapid/tasks`  
**Method :** `POST`

**URL Params :**
```
action=start-spy
Required
See
Common URL parameters
```

**Data Params :**
```
log-file={file-path}
Required
```

**Success :** NO_CONTENT (204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403), UNSUPPORTED_MEDIA (415), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "log-file=log.txt" -X POST "http://localhost/rw/rapid/tasks?action=start-spy"
```

**Notes :** Will request mastership internally (No need to ask explicitly). By default, log file will be created in HOME folder. Not supported in bootserver mode.

---

## Get RAPID Spy Logging status

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Get RAPID Spy Logging status

URL — /rw/rapid/tasks

**URL :** `/rw/rapid/tasks`  
**Method :** `GET`

**URL Params :**
```
resource=spy-status
Required
See
Common URL parameters
```

**Resources :**
```
rap-spy-status
status
Rapid spy logging status {Logging|Not Logging}
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/tasks?resource=spy-status"
```

**Notes :** Not supported in bootserver mode.

---

## Stop RAPID Spy Logging

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Stop RAPID Spy Logging

URL — /rw/rapid/tasks

**URL :** `/rw/rapid/tasks`  
**Method :** `POST`

**URL Params :**
```
action=stop-spy
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT (204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403), UNSUPPORTED_MEDIA (415), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/tasks?action=stop-spy"
```

**Notes :** Will request mastership internally (No need to ask explicitly). Not supported in bootserver mode.

---

## Activate/Deactivate rapid tasks

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Activate/Deactivate rapid tasks

URL — /rw/rapid/tasks

**URL :** `/rw/rapid/tasks`  
**Method :** `POST`

**URL Params :**
```
action=activate | deactivate
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/tasks?action=activate"
```

**Notes :** Not supported in bootserver mode
Mastership is taken internally if not taken explicitly by client.

---

## Get Program/Motion Pointer Sync State for all tasks

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Get Program/Motion Pointer Sync State for all tasks

URL — /rw/rapid/tasks

**URL :** `/rw/rapid/tasks`  
**Method :** `GET`

**URL Params :**
```
resource=sync-state
Required
type=program-pointer|motion-pointer
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/tasks?resource=sync-state&type=program-pointer"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on Build log change

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Subscribe on Build log change

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/tasks;buildlogchange')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-rap-buildlog-ev
task-name
taskname
build-count
build count
build-log-change
{SYS_CTRL_S_RAPID_SEMANTIC_ERROR|SYS_CTRL_S_RAPID_SYNTAX_ERROR|SYS_CTRL_S_OK}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID build log change
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks;buildlogchange&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks;buildlogchange&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID task

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task

---

## Get RAPID task state

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get RAPID task state

URL — /rw/rapid/tasks/{task}

**URL :** `/rw/rapid/tasks/{task}`  
**Method :** `GET`

**URL Params :**
```
continue-on-err={1|0}
Optional
Default value is 0. In case input is 1, the API continues execution even if any error occurs in between.
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-task
Rapid task resource
program Link to the program loaded into the task
modules Link to modules loaded into the task
name
: Task Name
type
: Type of Task
taskstate
: Task state can be empty, initiated,linked or loaded.
excstate
: Task execution state can be ready,stopped,started or uninitialized.
active
: Task is active or not
motiontask
: Motion Task is active or not
tasktype
: Task Type [Normal, Static, SemiStatic]
trust
: Task trust level [SysFail, SysHalt, SysStop, None]
taskID
: Task ID
execlevel
: Task Execution Level [None, Normal, Trap, User, Unknown]
execmode
: Task Execution Mode
exectype
: program execution Type [None, Normal, Inter (INTERRPUT), ExInter (EXTERNAL_INTERRUPT), UsRout (USER_ROUTINE), EvRout (EVENT_ROUTINE), Unknown (NA)]
prodentrypt
:RAPID program entry point either Main or Proc
bind_ref
: Task has configurated/Binded with Number [True, False]
task_in_forgnd
: Is this task running as foreground task? [True, False]
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404), FORBIDDEN(403)see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1
```

**Notes :** Retcode is provided if API fails.
Not supported in bootserver mode

---

## Get rapid task actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get rapid task actions

URL — /rw/rapid/tasks/{task}

**URL :** `/rw/rapid/tasks/{task}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Actions :**
```
loadmod
Load RAPID module
modulepath The RAPID module to load. Environment variables e.g. $HOME, $TEMP, etc can be used in the path.
replace True if current loaded module shall be replaced
unloadmod
Unload RAPID module
abortexeclevel
Abort execution of RAPID module
activate
Activate RAPID module
deactivate
Deactivate RAPID module
build
Build RAPID module
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/rapid/tasks/T_ROB1?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Load RAPID module into a rapid task

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Load RAPID module into a rapid task

URL — /rw/rapid/tasks/{task}

**URL :** `/rw/rapid/tasks/{task}`  
**Method :** `POST`

**URL Params :**
```
action=loadmod
Required
, form data see
Get rapid task actions
```

**Data Params :**
```
modulepath = {module_path}
Required
replace = {true | false}
Optional
Default value is false
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "modulepath=$HOME/mymod.mod" "http://localhost/rw/rapid/tasks/T_ROB1?action=loadmod"
```

**Notes :** Not supported in bootserver mode
Rapid Mastership Required

---

## Unload module from a rapid task

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Unload module from a rapid task

URL — /rw/rapid/tasks/{task}

**URL :** `/rw/rapid/tasks/{task}`  
**Method :** `POST`

**URL Params :**
```
action=unloadmod
Required
, form data see
Get rapid task actions
```

**Data Params :**
```
module={modulename}
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
NOT_FOUND(404)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "module=modulename" "http://localhost/rw/rapid/tasks/T_ROB1?action=unloadmod"
```

**Notes :** Not supported in bootserver mode
Rapid Mastership Required

---

## Abort current execution level

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Abort current execution level

URL — /rw/rapid/tasks/{task}

**URL :** `/rw/rapid/tasks/{task}`  
**Method :** `POST`

**URL Params :**
```
action=abortexeclevel
Required
```

**Data Params :**
```
None*
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/tasks/T_ROB1?action=abortexeclevel"
```

**Notes :** Not supported in bootserver mode
Rapid Mastership Required

---

## activate/deactivate rapid task

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › activate/deactivate rapid task

URL — /rw/rapid/tasks/{task}

**URL :** `/rw/rapid/tasks/{task}`  
**Method :** `POST`

**URL Params :**
```
action=activate | deactivate
Required
, form data see
Get rapid task actions
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/tasks/T_ROB1?action=activate"
```

**Notes :** Not supported in bootserver mode

---

## Get Activation Record

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get Activation Record

URL — /rw/rapid/tasks/{task_name}

**URL :** `/rw/rapid/tasks/{task_name}`  
**Method :** `GET`

**URL Params :**
```
resource=activation-record
stackframe={stack frame} The stack frame is a number starting with 1 for the current activation record, i.e., the activation record containing the user program pointer. The stack frame increases with one for each previous activation record until the entry point is reached.
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
rap-stackframe
Rapid-Symbol resource
execlevel
Execution level (Normal/Trap/User)
beg-row
begin position of row
beg-col
begin position of column
end-row
end position of row
end-col
begin position of column
stack-url
URL to the stack frame. In the format of RAPID/{task name}/%{stack frame}
routine-url
Routine URL
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404) ,FORBIDDEN(403), BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1?resource=activation-record&stackframe=1
```

**Notes :** Motors on
Load Rapid program
Run program

---

## Get Structural Change Count

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get Structural Change Count

URL — /rw/rapid/tasks/{task_name}

**URL :** `/rw/rapid/tasks/{task_name}`  
**Method :** `GET`

**URL Params :**
```
resource=task-struc-change-count See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
task-struc-change-count
Structural Change Count resource
change-count
: Relevant change occurs in the system
struc-change-count
: Load, Unload and renaming of modules. A rename is considered to be an unload/load, from the structural point of view.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1?resource=task-struc-change-count
```

**Notes :** Not supported in bootserver mode

---

## Get Preferable Data Types

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get Preferable Data Types

URL — /rw/rapid/tasks/{task_name}

**URL :** `/rw/rapid/tasks/{task_name}`  
**Method :** `GET`

**URL Params :**
```
resource=pref-data-types
Required
instruction={AliasIO}
Required
parameter={FromSignal}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
task-pref-data-types
Get Preferable Data Types resources
name-prefdattype
: name of the signal
type-prefdattype
: data type of signal
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1?resource=pref-data-types&instruction=AliasIO&parameter=FromSignal
```

**Notes :** Not supported in bootserver mode

---

## Get Program Pointer Sync State

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get Program Pointer Sync State

URL — /rw/rapid/tasks/{task_name}

**URL :** `/rw/rapid/tasks/{task_name}`  
**Method :** `GET`

**URL Params :**
```
resource=task-sync-state
Required
type=program-pointer
Required
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-sync-state
Rapid-sync-State resource
Program-Pointer-State
Program pointer state
Motion-Pointer-State
Motion pointer state
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403), NOT_FOUND(404), see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1?resource=task-sync-state&type=program-pointer
```

**Notes :** Not supported in bootserver mode

---

## Get Motion Pointer Sync State

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get Motion Pointer Sync State

URL — /rw/rapid/tasks/{task_name}

**URL :** `/rw/rapid/tasks/{task_name}`  
**Method :** `GET`

**URL Params :**
```
resource=task-sync-state
Required
type=motion-pointer
Required
```

**Data Params :**
```
None
```

**Success :** HTTP_OK, see
HTTP Status codes

**Error :** BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1?resource=task-sync-state&type=motion-pointer
```

**Notes :** Not supported in bootserver mode

---

## Link RAPID Task

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Link RAPID Task

URL — /rw/rapid/tasks/{task}

**URL :** `/rw/rapid/tasks/{task}`  
**Method :** `POST`

**URL Params :**
```
action=build
Required
, form data see
Get rapid task actions
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204) see
HTTP Status codes

**Error :** BAD REQUEST(400),FORBIDDEN(403),NOT_FOUND(404) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/tasks/T_ROB1?action=build"
```

**Notes :** Not supported in bootserver mode
RAPID Mastership Required

---

## Get Pallet

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get Pallet

URL — /rw/rapid/tasks/{task_name}

**URL :** `/rw/rapid/tasks/{task_name}`  
**Method :** `GET`

**URL Params :**
```
resource={pallet}&number={pallet_no}
Required
&start{page_no}&limit={elements_no}
optional
pallet_no. 1 - Common, pallet_no. 2 - Prog.Flow, pallet_no. 3 - Various, pallet_no. 4 - Settings, pallet_no. 5 - Motion&Proc., pallet_no. 6 - I/O, pallet_no. 7 - Communicate, pallet_no. 8 - Interrupts, pallet_no. 9 - Error Rec., pallet_no. 10 - System&Time, pallet_no. 11 - Mathematics, pallet_no. 12 - M.C 1, pallet_no. 13 - M.C 2, pallet_no. 14 - M.C 3, pallet_no. 15 - MotionSetAdv, pallet_no. 16 - Motion Adv., pallet_no. 17 - Ext.Computer, pallet_no. 18 - MultiTasking&MultiMove, pallet_no. 19 - RAPIDsupport, pallet_no. 20 - Calib&Service,
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-pallet
RAPID Pallet
Name
Pallet name
Instruction
Pallet instruction
Parameter
Pallet parameter
Alternative
Pallet alternative
Keyword
Pallet keyword
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost:7777/rw/rapid/tasks/T_ROB1?resource=pallet&number=9&start=1&limit=3
```

**Notes :** Not supported in bootserver mode

---

## Get Pallet Head

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Get Pallet Head

URL — /rw/rapid/tasks/{task_name}

**URL :** `/rw/rapid/tasks/{task_name}`  
**Method :** `GET`

**URL Params :**
```
resource={pallet-head}
Required
&start{page_no}&limit={elements_no}
optional
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-pallet-head
RAPID Pallet head
Name
Pallet name
Number
Pallet number
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost:7777/rw/rapid/tasks/T_ROB1?resource=pallet-head&start=1&limit=5
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on Rapid Task Change

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Subscribe on Rapid Task Change

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/tasks/<taskname>;taskchange')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-task-ev
change-count
Change count
task-name
Task name
module-name
Module name
program-name
Program name
changetype
{module|struc|program load|program name}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID task change
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1;taskchange&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1;taskchange&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** On subscription an empty initial event will be generated. Not supported in bootserver mode.

---

## Subscribe on Rapid PP Sync state change

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Subscribe on Rapid PP Sync state change

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/tasks/<taskname>;syncstatechange')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-syncstate-ev
sync-state
{on|off}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID task sync state change
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1;syncstatechange&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1;syncstatechange&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** On subscription an empty initial event will be generated followed by the current value. Not supported in bootserver mode.

---

## Subscribe on Rapid task pgmexecution state change

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Subscribe on Rapid task pgmexecution state change

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/tasks/<taskname>;excstate')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-execstate-ev
pgmtaskexec-state
{ready|started|stopped|initiated}
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID task sync state change
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1;excstate&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1;excstate&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** On subscription an empty initial event will be generated followed by the current value. Not supported in bootserver mode.

---

## Operations on rapid motion

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion

---

## Get rapid motion

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Get rapid motion

URL — /rw/rapid/tasks/{task}/motion

**URL :** `/rw/rapid/tasks/{task}/motion`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
robtarget
The target position from the home position.
jointtarget
The target position of the joint.
extjointstate
If any ext mechnical unit is attached than provide the extjoints.
mechunit
The unit in which robtarget, jointtarget and extjoint applies.
```

**Success :** HTTP_OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks/T_ROB1/motion"
```

**Notes :** Not supported in bootserver mode

---

## Get RobTarget

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Get RobTarget

URL — /rw/rapid/tasks/{task}/motion

**URL :** `/rw/rapid/tasks/{task}/motion`  
**Method :** `GET`

**URL Params :**
```
resource=robtarget
Required
tool={tool_name}
Optional
wobj={wobj_name}
Optional
```

**Data Params :**
```
None
```

**Resources :**
```
robtarget
The target position from the home position.
(x-z) Target positions.
(q1-q4) Orientation.
(cf1-cfx) Configuration.
(ej1-ej6) extjoints.
```

**Success :** HTTP_OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks/T_ROB1/motion?resource=robtarget&tool=tool0&wobj=wobj1"
```

**Notes :** Not supported in bootserver mode

---

## Get Joint Target

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Get Joint Target

URL — /rw/rapid/tasks/{task}/motion

**URL :** `/rw/rapid/tasks/{task}/motion`  
**Method :** `GET`

**URL Params :**
```
resource=jointtarget
Required
```

**Data Params :**
```
None
```

**Resources :**
```
jointtarget
The target position of the joint.
(j1-j6) Rotations.
(ej1-ej6) Target positions.
```

**Success :** HTTP_OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks/T_ROB1/motion?resource=jointtarget"
```

**Notes :** Not supported in bootserver mode

---

## Get mechanical units

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Get mechanical units

URL — /rw/rapid/tasks/{task}/motion

**URL :** `/rw/rapid/tasks/{task}/motion`  
**Method :** `GET`

**URL Params :**
```
resource=mechunit
Required
```

**Data Params :**
```
None
```

**Resources :**
```
rapid-mechunit
The Unit in which robtarget, jointtarget and extjoint applies.
name
name of mechnical unit.
mode
mode of mechnical unit.
type
type of mechnical unit.
```

**Success :** OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks/T_ROB1/motion?resource=mechunit"
```

**Notes :** Not supported in bootserver mode

---

## Get external joint states

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Get external joint states

URL — /rw/rapid/tasks/{task}/motion

**URL :** `/rw/rapid/tasks/{task}/motion`  
**Method :** `GET`

**URL Params :**
```
resource=extjointstate
Required
```

**Data Params :**
```
None
```

**Resources :**
```
rapid-extjointstate
If any ext mechnical unit is attached than provide the extjoints.
(j1-j6) Joints 1-6 {linear|not_active|no_position|rotating}
```

**Success :** OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks/T_ROB1/motion?resource=extjointstate"
```

**Notes :** Not supported in bootserver mode

---

## Operations on rapid calib

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Operations on rapid calib

---

## Calibration for Displacement

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Operations on rapid calib › Calibration for Displacement

URL — /rw/rapid/tasks/{task}/motion/calib

**URL :** `/rw/rapid/tasks/{task}/motion/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=Displacement
Required
type=POSE2
Required
point1=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point2=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point3=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point4=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point5=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point6=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point7=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point8=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point9=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
point10=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}, {x2}, {y2}, {z2}, {q2_1}, {q2_2}, {q2_3}, {q2_4}]
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST (400) ,See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=Displacement&type=POSE2&point1=[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0]&point2=[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0]&point3=[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0]" -X POST "http://127.0.0.1/rw/rapid/tasks/T_ROB1/motion/calib"
```

---

## Calibration for Tcp

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on rapid motion › Operations on rapid calib › Calibration for Tcp

URL — /rw/rapid/tasks/{task}/motion/calib

**URL :** `/rw/rapid/tasks/{task}/motion/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=TCP
Required
type=POSE
Required
tolerance={tolerance_value}
Required
point1=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point2=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point3=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point4=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point5=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point6=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point7=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point8=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point9=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
point10=[{x}, {y}, {z}, {q1}, {q2}, {q3}, {q4}]
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK (200), see
HTTP Status codes

**Error :** BAD_REQUEST (400) ,See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=TCP&type=POSE&tolerance=0&point1=[0, 0, 0, 1, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0]" -X POST "http://127.0.0.1/rw/rapid/tasks/T_ROB1/motion/calib"
```

---

## Operations on RAPID program

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program

---

## Get RAPID program resource

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Get RAPID program resource

URL — /rw/rapid/tasks/{task}/program

**URL :** `/rw/rapid/tasks/{task}/program`  
**Method :** `GET`

**URL Params :**
```
continue-on-err={1|0}
Optional
Default value is 0. In case input is 1, the API continues execution even if any error occurs in between.
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
rap-program
Rapid program resource
name
Program name
entrypoint
The program entry is the point PP will move to when "PP to main is called".
rap-program-breakpoint-li
Rapid program breakpoint resource
rap-builderrs-li
Rapid program builderrors resource
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/tasks/T_ROB1/program
"
```

**Notes :** Not supported in bootserver mode

---

## Get rapid program actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Get rapid program actions

URL — /rw/rapid/tasks/{task}/program

**URL :** `/rw/rapid/tasks/{task}/program`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
loadprog
Load RAPID program into a task
progpath Path on disk from where the program shall be loaded
loadmode {add | replace}
unloadprog
Unload program from task
save
Save program
path Path of the RAPID program.
setname
Set program name
name Program name.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/tasks/T_ROB1/program?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Load program into a rapid task

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Load program into a rapid task

URL — /rw/rapid/tasks/{task}/program

**URL :** `/rw/rapid/tasks/{task}/program`  
**Method :** `POST`

**URL Params :**
```
action=loadprog
Required
, form data see
Get rapid program actions
```

**Data Params :**
```
progpath={program path}
Required
loadmode={add | replace}
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST -d "progpath=$HOME/myprog.pgf" "http://localhost:7777/rw/rapid/tasks/T_ROB2/program?action=loadprog"
```

**Notes :** Not supported in bootserver mode

---

## Unload program from a rapid task

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Unload program from a rapid task

URL — /rw/rapid/tasks/{task}/program

**URL :** `/rw/rapid/tasks/{task}/program`  
**Method :** `POST`

**URL Params :**
```
action=unloadprog
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks/T_ROB1/program?action=unloadprog"
```

**Notes :** Not supported in bootserver mode

---

## Save program

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Save program

URL — /rw/rapid/tasks/{task}/program

**URL :** `/rw/rapid/tasks/{task}/program`  
**Method :** `POST`

**URL Params :**
```
action=save
Required
```

**Data Params :**
```
path={program_path}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "path=$HOME/myprog" -X POST "http://127.0.0.1/rw/rapid/tasks/T_ROB1/program?action=save"
```

**Notes :** Not supported in bootserver mode.

---

## Set program name

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Set program name

URL — /rw/rapid/tasks/{task}/program

**URL :** `/rw/rapid/tasks/{task}/program`  
**Method :** `POST`

**URL Params :**
```
action=setname
Required
```

**Data Params :**
```
name={program_name}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=myprog" -X POST "http://127.0.0.1/rw/rapid/tasks/T_ROB1/program?action=setname"
```

**Notes :** Not supported in bootserver mode.

---

## Set Entry Point

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Set Entry Point

URL — /rw/rapid/tasks/{task}/program

**URL :** `/rw/rapid/tasks/{task}/program`  
**Method :** `POST`

**URL Params :**
```
action=set-entrypoint
Required
, form data see
Get rapid task actions
```

**Data Params :**
```
routine= {routine-name}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400),FORBIDDEN(403),NOT_FOUND(404) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "routine=myroutine" -X POST "http://127.0.0.1/rw/rapid/tasks/T_ROB1/program?action=set-entrypoint"
```

**Notes :** Not supported in bootserver mode
Rapid mastership is required

---

## Operations on RAPID build errors

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Operations on RAPID build errors

---

## Get Build Errors

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Operations on RAPID build errors › Get Build Errors

URL — /rw/rapid/tasks/{task}/program/builderror

**URL :** `/rw/rapid/tasks/{task}/program/builderror`  
**Method :** `GET`

**URL Params :**
```
limit={limit_value}
Optional
start={start_value}
Optional
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
start
Reference to where the retrieval of build errors should start. Set to 1 to start from the beginning. The value returned can be used in the next call.
limit
The maximal number of elements to retrieve
prev
Link to previous page (Will be absent if there is no prev page)
next
Link to next page (Will be absent if there is no next page)
rap-builderrs
ModuleName
Module name
row
Row number
column
Column number
error
RAPID build error
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404),BAD_REQUEST(400), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/tasks/T_ROB1/program/builderror?start=1&limit=2
"
```

**Notes :** Default value of start is 1 and maximum value of limit is 30(maximum supported by RAPID).
Absence of prev and next link indicates first and last page respectively.
Not supported in bootserver mode.

---

## Operations on RAPID breakpoint

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Operations on RAPID breakpoint

---

## Get RAPID breakpoint actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Operations on RAPID breakpoint › Get RAPID breakpoint actions

URL — /rw/rapid/tasks/{task}/program/breakpoint

**URL :** `/rw/rapid/tasks/{task}/program/breakpoint`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/rapid/tasks/T_ROB1/program/breakpoint?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Set break point

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Operations on RAPID breakpoint › Set break point

URL — /rw/rapid/tasks/{task}/program/breakpoint

**URL :** `/rw/rapid/tasks/{task}/program/breakpoint`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
```

**Data Params :**
```
module={module-name}
Required
row={row_no}
Required
column={col_no}
Required
```

**Success :** NO_CONTENT(204) , see
HTTP Status codes

**Error :** HTTP_BAD_REQUEST(400), FORBIDDEN(403), NOT_FOUND(404) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST -d "module=MainModule&row=15&column=3" "http://127.0.0.1/rw/rapid/tasks/T_ROB1/program/breakpoint?action=set"
```

**Notes :** Mastership is required
Not supported in bootserver mode

---

## Get break points

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program › Operations on RAPID breakpoint › Get break points

URL — /rw/rapid/tasks/{task}/program/breakpoint

**URL :** `/rw/rapid/tasks/{task}/program/breakpoint`  
**Method :** `GET`

**URL Params :**
```
start={start_value}
limit={limit_value}, See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-program-breakpoint
module-name
Name of the module
start-row
Start row number
start-col
Start column number
end-row
End row number
end-col
End col number
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404)
BAD_REQUEST(400)
see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/tasks/T_ROB1/program/breakpoint?start=1&limit=2"
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID program PCP

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP

---

## Get RAPID task Motion&Program pointer positions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Get RAPID task Motion&Program pointer positions

URL — /rw/rapid/tasks/{task}/pcp

**URL :** `/rw/rapid/tasks/{task}/pcp`  
**Method :** `GET`

**URL Params :**
```
None*
```

**Data Params :**
```
None*
```

**Resources :**
```
pcp-info
Rapid task pcp resource
modulemame
Current running module.
routinename
Current routine name in module where progarm pointer and motion pointer located .
changecount
Number of time progarm pointer or motion pointer relocated .
executiontype
ExecutionType can be No execution context, Normal, Interrupt, extrenal interrupt, user routine, event routine.
beginposition
begin position of programe poionter.
endposition
end position of programe poionter.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1/pcp
```

**Notes :** Not supported in bootserver mode

---

## Get RAPID task pcp actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Get RAPID task pcp actions

URL — /rw/rapid/tasks/{task}/pcp

**URL :** `/rw/rapid/tasks/{task}/pcp`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Actions :**
```
setPPtocursor
Set the ProgramPointer(PP) to cursor
module
The RAPID module in which requested to set the PP
line
Line number in RAPID module
column
Column
routine
Name of routine to which PP need to be set
userlevel
Needs to be true, in case of setting the PP in user module. Otherwise false (optional).
setpptoroutine
Set the ProgramPointer(PP) to routine
set-pp-prev-inst
Set the ProgramPointer(PP) to previous instruction
set-pp-next-inst
Set the ProgramPointer(PP) to next instruction
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/rapid/tasks/T_ROB1/pcp?action=show
"
```

**Notes :** Not supported in bootserver mode

---

## Set the Program pointer(PP) position to cursor

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Set the Program pointer(PP) position to cursor

URL — /rw/rapid/tasks/{task}/pcp

**URL :** `/rw/rapid/tasks/{task}/pcp`  
**Method :** `POST`

**URL Params :**
```
action=set-pp-cursor
Required
, form data see
Get RAPID task pcp actions
```

**Data Params :**
```
module= {module name}
Required
routine= {routine name}
Required
line= {line_number}
Required
column= {column_number name}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "module=modulename&line=6&column=14&routine=routinename" -X POST "http://localhost/rw/rapid/tasks/T_ROB1/pcp?action=set-pp-cursor"
```

**Notes :** Line number and Column number should be in given routine range.**
Not supported in bootserver mode
Rapid Mastership Required

---

## Set the Program pointer(PP) position to routine

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Set the Program pointer(PP) position to routine

URL — /rw/rapid/tasks/{task}/pcp

**URL :** `/rw/rapid/tasks/{task}/pcp`  
**Method :** `POST`

**URL Params :**
```
action=set-pp-routine
Required
, form data see
Get RAPID task pcp actions
```

**Data Params :**
```
module= {module name}
Required
routine= {routine name}
Required
userlevel= {true | false}
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "module=modulename&routine=routinename&userlevel=true" -X POST "http://localhost/rw/rapid/tasks/T_ROB1/pcp?action=set-pp-routine"
```

**Notes :** Not supported in bootserver mode.
Controller needs to be in auto mode.

---

## Set the Program pointer(PP) position to routine by URL

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Set the Program pointer(PP) position to routine by URL

URL — /rw/rapid/tasks/{task}/pcp

**URL :** `/rw/rapid/tasks/{task}/pcp`  
**Method :** `POST`

**URL Params :**
```
action=set-pp-routine-from-url
Required
, form data see
Get RAPID task pcp actions
```

**Data Params :**
```
module= {module name}
Required
routine= {routine name}
Required
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "module=modulename&routine=routinename" -X POST "http://localhost/rw/rapid/tasks/T_ROB1/pcp?action=set-pp-routine-from-url"
```

**Notes :** Not supported in bootserver mode.
Controller needs to be in auto mode.

---

## Set the Program pointer(PP) position to previous instruction

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Set the Program pointer(PP) position to previous instruction

URL — /rw/rapid/tasks/{task}/pcp

**URL :** `/rw/rapid/tasks/{task}/pcp`  
**Method :** `POST`

**URL Params :**
```
action=set-pp-prev-inst
Required
, form data see
Get RAPID task pcp actions
```

**Data Params :**
```
None*
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/tasks/T_ROB1/pcp?action=set-pp-prev-inst"
```

**Notes :** Not supported in bootserver mode.
Controller needs to be in auto mode.

---

## Set the Program pointer(PP) position to next instruction

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Set the Program pointer(PP) position to next instruction

URL — /rw/rapid/tasks/{task}/pcp

**URL :** `/rw/rapid/tasks/{task}/pcp`  
**Method :** `POST`

**URL Params :**
```
action=set-pp-next-inst
Required
, form data see
Get RAPID task pcp actions
```

**Data Params :**
```
None*
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/rapid/tasks/T_ROB1/pcp?action=set-pp-next-inst"
```

**Notes :** Not supported in bootserver mode.
Controller needs to be in auto mode.

---

## Subscribe on Program Pointer

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Subscribe on Program Pointer

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/tasks/<taskname>/pcp;programpointerchange')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-pcp-ev
module-nam
Module name
routine-name
routine name
BegPosLine
Begining Line number of the current PCP
BegPosCol
Begining Column number of the current PCP
EndPosLine
Ending Line number of the current PCP
EndPosCol
Ending Column number of the current PCP
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID program pointer
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1/pcp;programpointerchange&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1/pcp;programpointerchange&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** On subscription an empty initial event will be generated followed by the current value. Not supported in bootserver mode

---

## Subscribe on Motion Pointer

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program PCP › Subscribe on Motion Pointer

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/tasks/<taskname>/pcp;motionpointerchange')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-pcp-ev
module-nam
Module name
routine-name
routine name
BegPosLine
Begining Line number of the current PCP
BegPosCol
Begining Column number of the current PCP
EndPosLine
Ending Line number of the current PCP
EndPosCol
Ending Column number of the current PCP
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID motion pointer
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1/pcp;motionpointerchange&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/tasks/T_ROB1/pcp;motionpointerchange&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** On subscription an empty initial event will be generated followed by the current value. Not supported in bootserver mode

---

## Operations on RAPID service routine

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID service routine

---

## Get RAPID service routine

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID service routine › Get RAPID service routine

URL — /rw/rapid/tasks/{task}/serviceroutine

**URL :** `/rw/rapid/tasks/{task}/serviceroutine`  
**Method :** `GET`

**URL Params :**
```
start={PageNumber}
Optional
limit={no. of elements}
Optional
allread={TRUE|FALSE}
Optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
rap-task-routine
Rapid task serviceroutine
Routine_name: Name of the Routine
URL_to_Routine: URL to Routine
service-routine: TRUE: service routine, FALSE: normal routine
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), NOT_FOUND(404) HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics"
http://localhost/rw/rapid/tasks/T_ROB1/serviceroutine
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID program counter position

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program counter position

---

## Get RAPID Program counter position

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID tasks › Operations on RAPID task › Operations on RAPID program counter position › Get RAPID Program counter position

URL — /rw/rapid/tasks/{task}/execution

**URL :** `/rw/rapid/tasks/{task}/execution`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), NOT_FOUND(404), see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/tasks/T_ROB1/execution"
```

**Notes :** Not supported in bootserver mode

---

## Operations on RAPID UI instructions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions

---

## Get UI instruction resource

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Get UI instruction resource

URL — /rw/rapid/uiinstr

**URL :** `/rw/rapid/uiinstr`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-active-li
Active UI instruction resource list
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT FOUND(404), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/uiinstr"
```

**Notes :** Not supported in bootserver mode

---

## Get UI instruction actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Get UI instruction actions

URL — /rw/rapid/uiinstr

**URL :** `/rw/rapid/uiinstr`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
sub-uievent
resources
selected resource.
res
resource name.
priority
Priority of the UI instruction.
selected
selected UI instruction.
```

**Actions :**
```
subscribe
Subscribe on UI instruction
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/uiinstr?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on UI instruction

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Subscribe on UI instruction

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources=1&1=/rw/rapid/uiinstr;uievent&1-p=0
```

**Resources :**
```
rap-ui-ev
UI instruction event
instr
- Instruction is one of {IAlphaEntry | IListView | IMessageBox | IMsgBox | INumEntry | INumTune | IShow | TPErase | TPReadFK | TPReadNum | TPShow | TPWrite}
event
- Event is one of {SEND | POST | ABORT}
stack
- The stack url, a link to the UI instruction parameters.
execlv
- Rapid task execution level.
msg
- Line of text
```

**Success :** CREATED(201), see
HTTP Status codes

**Error :** BAD_REQUEST(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
Subscribe on UI Events
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/rapid/uiinstr;uievent&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/rapid/uiinstr;uievent&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Operations on Active UI Instruction

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Operations on Active UI Instruction

---

## Get Active UI Instruction

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Operations on Active UI Instruction › Get Active UI Instruction

URL — /rw/rapid/uiinstr/active

**URL :** `/rw/rapid/uiinstr/active`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-uiactive-li
The pending UI instruction resource
instr
- Instruction is one of {IAlphaEntry | IListView | IMessageBox | IMsgBox | INumEntry | INumTune | IShow | TPErase | TPReadFK | TPReadNum | TPShow | TPWrite}.
event
- Event is one of {SEND | POST | ABORT}.
stack
- The stack url, a link to the UI instruction parameters.
execlv
- Rapid task execution level.
msg
- Line of text
params
- Link to UI message parameters. The parameters are defined in the RAPID manual.
param
- Link to UI message parameter.
```

**Success :** HTTP_OK(200), if there is an active UI instruction.

**Error :** BAD REQUEST(400),NOT_FOUND(404) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/uiinstr/active"
```

**Notes :** Not supported in bootserver mode

---

## Get Active UI instruction actions

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Operations on Active UI Instruction › Get Active UI instruction actions

URL — /rw/rapid/uiinstr/active

**URL :** `/rw/rapid/uiinstr/active`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action Forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
set
value
value of UI param
```

**Actions :**
```
set
see
Update an Active UI Instruction Parameter
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** Bad Request(400), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/uiinstr/active?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Update an Active UI Instruction Parameter

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Operations on Active UI Instruction › Update an Active UI Instruction Parameter

URL — /rw/rapid/uiinstr/active/param/{stackurl}/{uiparam}

**URL :** `/rw/rapid/uiinstr/active/param/{stackurl}/{uiparam}`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
, form data see
Get rapid task actions
See
Common URL parameters
```

**Data Params :**
```
value={value}
For example, TPFK3 can accept a value like
"0"
and TPCompleted can accept a value like
TRUE
```

**Success :** NO_CONTENT(204), see
HTTP Status codes

**Error :** BAD REQUEST(400),NOT_FOUND(404),FORBIDDEN(403) see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "value=0" -X POST "http://127.0.0.1/rw/rapid/uiinstr/active/param/RAPID/T_ROB1/%$104/TPFK3?action=set"
curl --digest -u "Default User":robotics -d "value=TRUE" X POST "http://127.0.0.1/rw/rapid/uiinstr/active/param/RAPID/T_ROB1/%$104/TPCompleted?action=set"
```

**Notes :** -Not supported in bootserver mode
-{stackurl} ends with a variable number, which can be obtained from "Get Active UI Instruction" API.
-RAPID program should be running
-Example of {uiparam} are TPFK1, TPFK2, TPFK3, TPCompleted etc

---

## Get parameter value for an active UI instruction

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Operations on Active UI Instruction › Get parameter value for an active UI instruction

URL — /rw/rapid/uiinstr/active/param/{stackurl}/{uiparam}

**URL :** `/rw/rapid/uiinstr/active/param/{stackurl}/{uiparam}`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-uiparam
UI param
value
Requested UI parameter value
```

**Success :** HTTP_OK(200), if there is an active UI instruction.

**Error :** BAD_REQUEST(400) , NOT_FOUND(404) see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/uiinstr/active/param/RAPID/T_ROB1/%25%2499/Result"
```

**Notes :** Not supported in bootserver mode

---

## Get active UI instruction parameters

**Chemin :** RobotWare Services › RAPID Service › Operations on RAPID UI instructions › Operations on Active UI Instruction › Get active UI instruction parameters

URL — /rw/rapid/uiinstr/active/params/{stackurl}

**URL :** `/rw/rapid/uiinstr/active/params/{stackurl}`  
**Method :** `GET`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-uiparam-li
UI instruction parameter
title
Parameter name
value
Parameter value
```

**Success :** HTTP_OK(200), if there is an active UI instruction.

**Error :** BAD_REQUEST(400), NOT_FOUND(404), see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://127.0.0.1/rw/rapid/uiinstr/active/params/RAPID/T_ROB1/%25%2499"
```

**Notes :** Not supported in bootserver mode

---

## Operations on Rapid taskpanel

**Chemin :** RobotWare Services › RAPID Service › Operations on Rapid taskpanel

---

## Get user modify from taskpanel

**Chemin :** RobotWare Services › RAPID Service › Operations on Rapid taskpanel › Get user modify from taskpanel

URL — /rw/rapid/taskselection

**URL :** `/rw/rapid/taskselection`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
rap-taskselection
Rapid tasks user modify flag.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400) , see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/rapid/taskselection"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on Tasks panel change

**Chemin :** RobotWare Services › RAPID Service › Operations on Rapid taskpanel › Subscribe on Tasks panel change

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
*<identifier>*=The subscription resource URI (The URI here is: '/rw/rapid/taskselection;taskpanelchange')
*<identifier>-p*=The priority associated with the subscription resource.
```

**Resources :**
```
rap-taskpanel-ev
change-count
number of times the changes occured
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID build log change
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/taskselection;taskpanelchange&1-p=0" "http://127.0.0.1/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/rapid/taskselection;taskpanelchange&1-p=1" "http://127.0.0.1/subscription"
```

**Notes :** Not supported in bootserver mode

---

## Operations on Rapid AliasIO

**Chemin :** RobotWare Services › RAPID Service › Operations on Rapid AliasIO

---

## Get AliasIO List

**Chemin :** RobotWare Services › RAPID Service › Operations on Rapid AliasIO › Get AliasIO List

URL — /rw/rapid/aliasio

**URL :** `/rw/rapid/aliasio`  
**Method :** `GET`

**URL Params :**
```
start={start position}
Optional
limit={number of aliasios}
Optional
```

**Data Params :**
```
None*
```

**Resources :**
```
rap-alias-io
Rapid AliasIO resource
alias-name
IO signal alias name
signal-name
name of the IO signal
type
IO signal type {DI/ DO/ AI/ AO/ GI/ GO}
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://127.0.0.1/rw/rapid/aliasio?start=0
"
```

**Notes :** Not supported in bootserver mode

---

## System service

**Chemin :** RobotWare Services › System service

---

## System Information

**Chemin :** RobotWare Services › System service › System Information

URL — /rw/system

**URL :** `/rw/system`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
sys-system-li
below system information tags are valid only for RC, not VC
major
RobotWare major version
minor
RobotWare minor version
build
RobotWare build version
revision
RobotWare revision version
sub_revision
RobotWare sub revision version
buildtag
RobotWare build tag
robapi_compatibility_revision
Robapi compatibility revision
title
RobotWare system title
type
RobotWare system type
description
RobotWare system description
date
RobotWare system date
mctimestamp
MC file timestamp
below system information tags are valid for both RC and VC
rwversion
RobotWare version
rwversionname
RobotWare version name
name
RobotWare System name
sysid
System GUID
starttm
system Startup time
sys-options-li
option
Option
sys-products-li
products
Returns Installed Products.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system"
```

**Notes :** Not supported in bootserver mode

---

## Get robot type

**Chemin :** RobotWare Services › System service › Get robot type

URL — /rw/system/robottype

**URL :** `/rw/system/robottype`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
robottype
type of robot.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system/robottype"
```

**Notes :** Not supported in bootserver mode.
The API supports only ABB standard robots. Positioners, track motion etc. are not supported.
In case, there is no ABB standard robots, NO_CONTENT will be returned.

---

## System Option Resource

**Chemin :** RobotWare Services › System service › System Option Resource

---

## System Options

**Chemin :** RobotWare Services › System service › System Option Resource › System Options

URL — /rw/system/options

**URL :** `/rw/system/options`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
sys-options-li
option
Option
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system/options"
```

**Notes :** Not supported in bootserver mode

---

## System Energy Resource

**Chemin :** RobotWare Services › System service › System Energy Resource

---

## Get System Energy Actions

**Chemin :** RobotWare Services › System service › System Energy Resource › Get System Energy Actions

URL — /rw/system/energy

**URL :** `/rw/system/energy`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
Returns action forms for this resource
See
Common URL parameters
```

**Data Params :**
```
None
```

**Actions :**
```
subscribe
subscribe to system energy information.
reset-accumulated-energy
Resets System Accumulated Energy.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system/energy?action=show"
```

**Notes :** Not supported in bootserver mode

---

## System Energy Info Change Count

**Chemin :** RobotWare Services › System service › System Energy Resource › System Energy Info Change Count

URL — /rw/system/energy

**URL :** `/rw/system/energy`  
**Method :** `GET`

**URL Params :**
```
resource = change-count
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
sys-energy-changecount-li
change-count
Returns the change count of the measurement. The value is increased when a new measurement is available.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system/energy?resource=change-count"
```

**Notes :** Not supported in bootserver mode

---

## Reset Accumulated Energy

**Chemin :** RobotWare Services › System service › System Energy Resource › Reset Accumulated Energy

URL — /rw/system/energy

**URL :** `/rw/system/energy`  
**Method :** `POST`

**URL Params :**
```
action=reset
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400),NOT_FOUND(404)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system/energy?action=reset"
```

**Notes :** Not supported in bootserver mode

---

## System Energy

**Chemin :** RobotWare Services › System service › System Energy Resource › System Energy

URL — /rw/system/energy

**URL :** `/rw/system/energy`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
sys-energy-state-li
state
- contains the status of the operation, 0 when the data is valid. if stat is -1 the measurement is not valid.
energy-state
returns the energy state of the system such as blocked, paused, not-paused, resuming, pausing, going-to-sleep or sleep.
change-count
returns the change count of the measurement. The value is increased when a new measurement is available.
time-stamp
time stamp for measurement.
reset-time
time for reset of accumulated energy value.
interval-length
measurement interval length, can be used to compute the average power consumption.
interval-energy
total energy for current measurement interval.
accumulated-energy
total accumulated energy from last reset, sampled in the beginning of the measurement interval.
sys-energy-mec-li
title
name of mechanical unit.
sys-energy-axis-li
title
axis number in mechanical unit.
interval-energy
energy value of the axis for current interval.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system/energy"
```

**Notes :** Not supported in bootserver mode

---

## Subscribe on System Energy Changes.

**Chemin :** RobotWare Services › System service › System Energy Resource › Subscribe on System Energy Changes.

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
resources
= An identifier
Required
<identifier> = The subscription resource URI (The URI here is: '/rw/system/energy')
Required
<identifier>-p = The priority associated with the subscription resource
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** UNSUPPORTED_MEDIA(415),BAD_REQUEST(400)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/system/energy&1-p=0" -X POST "http://localhost/subscription"
curl --digest -u "Default User":robotics -d "resources=1&1=/rw/system/energy&1-p=1" -X POST "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode

---

## System License Resource

**Chemin :** RobotWare Services › System service › System License Resource

---

## Get System Robotware License

**Chemin :** RobotWare Services › System service › System License Resource › Get System Robotware License

URL — /rw/system/license

**URL :** `/rw/system/license`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
license
System robotware license.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/system/license"
```

**Notes :** Not supported in bootserver mode.

---

## System Products Resource

**Chemin :** RobotWare Services › System service › System Products Resource

---

## Get Installed Products

**Chemin :** RobotWare Services › System service › System Products Resource › Get Installed Products

URL — /rw/system/products

**URL :** `/rw/system/products`  
**Method :** `GET`

**URL Params :**
```
name={product-name}
optional
```

**Data Params :**
```
None
```

**Resources :**
```
title
RobotWare system product title
version-name
RobotWare system product version name
```

**Success :** HTTP_OK(200), NO_CONTENT(204)
See
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors
See
Robot controller return codes

**Sample Call :**
```bash
`curl –digest -u "Default User":robotics " "
http://localhost:7777/rw/system/products/
"
```

**Notes :** In case, there is no products, NO_CONTENT(204) will be returned.

---

## RobotWare return codes service

**Chemin :** RobotWare Services › RobotWare return codes service

Example — Update a RAPID variable without required master ship.

**URL :** `/rw/rapid/symbol/data/RAPID/T_ROB1/user/reg1?action=set.`  
---

## Get a list of RobotWare return codes

**Chemin :** RobotWare Services › RobotWare return codes service › Get a list of RobotWare return codes

URL — /rw/retcode

**URL :** `/rw/retcode`  
**Method :** `GET`

**URL Params :**
```
code={code}
optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
err-descr-li
title
The error code or success code as number
name
The error code or success code as string
code
The error code or success code as number
severity
Success, Warning or Error
description
Short description of the error code
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://192.168.8.105/rw/retcode"
```

**Notes :** Error description are only available in English and XML is the only supported format.
Not supported in bootserver mode

---

## Devices service

**Chemin :** RobotWare Services › Devices service

---

## Devices tree information

**Chemin :** RobotWare Services › Devices service › Devices tree information

URL — /rw/devices

**URL :** `/rw/devices`  
**Method :** `GET`

**URL Params :**
```
Lang={lang}
Optional
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
dev-id-li
name
resource name
dev-propint-li
name
resource name
value
value is of type integer
unit
resource unit if it exists
dev-propstr-li
name
resource name
value
value is of type string
unit
resource unit if it exists
dev-proptid-li
name
resource name
value
value is of type textID, i.e. provides the status of resource. ex: OK, ENABLED etc
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), NOT_FOUND(404)
HTTP Errors, see
HTTP Status codes
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/devices"
curl --digest -u "Default User":robotics "http://localhost/rw/devices/hw_devices/CONTROLLER/COMPUTER_SYSTEM/SERIAL_PORTS/COM1_PORT"
```

**Notes :** Not supported in bootserver mode.

---

## Motion System

**Chemin :** RobotWare Services › Motion System

---

## Get Motion System

**Chemin :** RobotWare Services › Motion System › Get Motion System

URL — /rw/motionsystem

**URL :** `/rw/motionsystem`  
**Method :** `GET`

**URL Params :**
```
continue-on-err={1|0}
Continues the execution even if any error occurs and default value is 0
resource={modal-payload-mode|absacc-active|poll-rate|change-count|mechunit-name}.This URL parameter can be used for filtering.
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
motionsystem = domain name
change-count = counter to keep count for every change in the motion system(domain)
mechunit-name = name of the mechanical unit
poll-rate = polling rate
err-state = error state
err-count = error count
modal-payload_mode = modal payload mode
absacc-active = absolute accuracy active
mechunit, motionsupervision, jogdata, incstepsizes = different functionalities which come under the motionsystem root resource. Refer individual documents for more information.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem"
```

---

## Get Motion System action

**Chemin :** RobotWare Services › Motion System › Get Motion System action

URL — /rw/motionsystem

**URL :** `/rw/motionsystem`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem?action=show"
```

---

## Set Mechunit for jogging

**Chemin :** RobotWare Services › Motion System › Set Mechunit for jogging

URL — /rw/motionsystem

**URL :** `/rw/motionsystem`  
**Method :** `POST`

**URL Params :**
```
action=set-mechunit
Required
See
Common URL parameters
```

**Data Params :**
```
mechunit-name={mechunit}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mechunit-name=ROB_1" -X POST "http://localhost/rw/motionsystem?action=set-mechunit"
```

---

## Perform Jogging

**Chemin :** RobotWare Services › Motion System › Perform Jogging

URL — /rw/motionsystem

**URL :** `/rw/motionsystem`  
**Method :** `POST`

**URL Params :**
```
action=jog
Required
See
Common URL parameters
```

**Data Params :**
```
axis1={axis1}
Required
axis2={axis2}
Required
axis3={axis3}
Required
axis4={axis4}
Required
axis5={axis5}
Required
axis6={axis6}
Required
ccount={ccount}
Required
inc-mode={User | Medium | Small | Large} (default value = no increment)
```

**Success :** NO_CONTENT(204) see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "axis1=900&axis2=0&axis3=0&axis4=0&axis5=0&axis6=0&ccount=0&inc-mode=Large" -X POST "http://localhost/rw/motionsystem?action=jog"
```

---

## Set Robo Target Position

**Chemin :** RobotWare Services › Motion System › Set Robo Target Position

URL — /rw/motionsystem

**URL :** `/rw/motionsystem`  
**Method :** `POST`

**URL Params :**
```
action=positiontarget
Required
See
Common URL parameters
```

**Data Params :**
```
pos-x={value of x}
Required
pos-y={value of y}
Required
pos-z={value of z}
Required
orient-q1={value of q1}
Required
orient-q2={value of q2}
Required
orient-q3={value of q3}
Required
orient-q4={value of q4}
Required
config-j1={value of j1}
Required
config-j4={value of j4}
Required
config-j6={value of j6}
Required
config-jx={value of jx}
Required
extjoint-1={value of ej1}
Required
extjoint-2={value of ej2}
Required
extjoint-3={value of ej3}
Required
extjoint-4={value of ej4}
Required
extjoint-5={value of ej5}
Required
extjoint-6={value of ej6}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "pos-x=634.609&pos-y=50.7298&pos-z=432.9419&orient-q1=0.4932235&orient-q2=-0.03467758&orient-q3=0.8689883&orient-q4=0.01968242&config-j1=0&config-j4=0&config-j6=0&config-jx=0&extjoint-1=0&extjoint-2=8.999999&extjoint-3=8.999999&extjoint-4=8.999999&extjoint-5=8.999999&extjoint-6=8.999999" -X POST "http://localhost/rw/motionsystem?action=positiontarget"
```

---

## Get check change count

**Chemin :** RobotWare Services › Motion System › Get check change count

URL — /rw/motionsystem/checkchangecount

**URL :** `/rw/motionsystem/checkchangecount`  
**Method :** `GET`

**URL Params :**
```
changecount={changecount}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
changestate
changecount changed or not, {TRUE|FALSE}
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/checkchangecount?changecount=0"
```

---

## Subscribe on Error EventChange

**Chemin :** RobotWare Services › Motion System › Subscribe on Error EventChange

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**Data Params :**
```
resources
=An identifier
Required
*<identifier>*=The subscription resource URI (The URI here is: '/rw/motionsystem/errorstate;erroreventchange')
Required
*<identifier>-p*=The priority associated with the subscription resource.
Required
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource**
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/motionsystem/errorstate;erroreventchange&1-p=0" "http://localhost/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/motionsystem/errorstate;erroreventchange&1-p=1" "http://localhost/subscription"
```

**Notes :** On subscription an empty initial event will be generated. Not supported in bootserver mode.

---

## Operations on Error State

**Chemin :** RobotWare Services › Motion System › Operations on Error State

---

## Get Error State

**Chemin :** RobotWare Services › Motion System › Operations on Error State › Get Error State

URL — /rw/motionsystem/errorstate

**URL :** `/rw/motionsystem/errorstate`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Resources :**
```
ms-errorstate
err-state
Error state
HPJ_OK
HPJ_ERR_UNIT_NOT_ACTIVE
If you are trying to jog a mechanical unit where the activation fails
HPJ_ERR_UNVALID_UNCALIBRATED_JOG_MOTION_TYPE
if you are trying to jog an uncalibrated robot in any of the following modes: Linear, Align, Goto Pose, Arm-angle
HPJ_ERR_UNNORM_QUAT
If an unnormalized quaternion reaches the jogging task. Can come from any of the following: tool definition, tool-load, total load, work object.
HPJ_ERR_ERRONEOUS_TOOL_MASS
If the mass is negative in any load definition (tool load, load, or total load)
MECMAP_ERR_ROBHOLD_MISMATCH
If there is a conflict between robhold in the tool and robhold in the work object
HPJ_ERR_WOBJ_MECH_NOT_FOUND
If a unit used in coordinated jogging is not found
HPJ_ERR_UNVALID_JOG_MOTION_TYPE
If the chosen jogging mode is invalid.
err-count
Error count (If a new error occurs, count will be incremented.)
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/errorstate"
```

---

## Operations on Motion Supervision

**Chemin :** RobotWare Services › Motion System › Operations on Motion Supervision

---

## Get Motion Supervision

**Chemin :** RobotWare Services › Motion System › Operations on Motion Supervision › Get Motion Supervision

URL — /rw/motionsystem/motionsupervision

**URL :** `/rw/motionsystem/motionsupervision`  
**Method :** `GET`

**URL Params :**
```
mechunit={mechunit name}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/motionsupervision?mechunit=ROB_1"
```

---

## Get Motion Supervision Actions

**Chemin :** RobotWare Services › Motion System › Operations on Motion Supervision › Get Motion Supervision Actions

URL — /rw/motionsystem/motionsupervision

**URL :** `/rw/motionsystem/motionsupervision`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/motionsupervision?action=show"
```

---

## Set Motion Supervision Mode (Jog Supervision Mode)

**Chemin :** RobotWare Services › Motion System › Operations on Motion Supervision › Set Motion Supervision Mode (Jog Supervision Mode)

URL — /rw/motionsystem/motionsupervision

**URL :** `/rw/motionsystem/motionsupervision`  
**Method :** `POST`

**URL Params :**
```
action=set-mode
Required
See
Common URL parameters
```

**Data Params :**
```
mechunit-name={mechanical unit name}
Required
mode={True | False}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mechunit-name=ROB_1&mode=True" - POST "http://localhost/rw/motionsystem/motionsupervision?action=set-mode"
```

---

## Set Motion Supervision Sensitivity (Jog Supervision Sensitivity)

**Chemin :** RobotWare Services › Motion System › Operations on Motion Supervision › Set Motion Supervision Sensitivity (Jog Supervision Sensitivity)

URL — /rw/motionsystem/motionsupervision

**URL :** `/rw/motionsystem/motionsupervision`  
**Method :** `POST`

**URL Params :**
```
action=set-level
Required
See
Common URL parameters
```

**Data Params :**
```
mechunit-name= {mechunit}
Required
sensitivity={value}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mechunit-name=ROB_1&sensitivity=30" - POST "http://localhost/rw/motionsystem/motionsupervision?action=set-level"
```

---

## Get Motion Supervision Collision Prediction Mode

**Chemin :** RobotWare Services › Motion System › Operations on Motion Supervision › Get Motion Supervision Collision Prediction Mode

URL — /rw/motionsystem/motionsupervision

**URL :** `/rw/motionsystem/motionsupervision`  
**Method :** `GET`

**URL Params :**
```
action=collision-prediction-mode
Required
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/motionsupervision?action=collision-prediction-mode"
```

---

## Set Motion Supervision Collision Prediction Mode

**Chemin :** RobotWare Services › Motion System › Operations on Motion Supervision › Set Motion Supervision Collision Prediction Mode

URL — /rw/motionsystem/motionsupervision

**URL :** `/rw/motionsystem/motionsupervision`  
**Method :** `POST`

**URL Params :**
```
action=set-colpred-mode
Required
```

**Data Params :**
```
mode={true | false}
Required
```

**Success :** NO_CONTENT (204)

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mode=true" - POST "http://localhost/rw/motionsystem/motionsupervision?action=set-colpred-mode"
```

---

## Operations On Path Supervision

**Chemin :** RobotWare Services › Motion System › Operations On Path Supervision

---

## Get Path Supervision

**Chemin :** RobotWare Services › Motion System › Operations On Path Supervision › Get Path Supervision

URL — /rw/motionsystem/pathsupervision

**URL :** `/rw/motionsystem/pathsupervision`  
**Method :** `GET`

**URL Params :**
```
mechunit={mechunit}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
mode
Path supervision mode
level
Path supervision level
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/pathsupervision?mechunit=ROB_1"
```

---

## Get Path Supervision Actions

**Chemin :** RobotWare Services › Motion System › Operations On Path Supervision › Get Path Supervision Actions

URL — /rw/motionsystem/pathsupervision

**URL :** `/rw/motionsystem/pathsupervision`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
mode
Path supervision mode
level
Path supervision level
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/pathsupervision?action=show"
```

---

## Set Path Supervision Mode

**Chemin :** RobotWare Services › Motion System › Operations On Path Supervision › Set Path Supervision Mode

URL — /rw/motionsystem/pathsupervision

**URL :** `/rw/motionsystem/pathsupervision`  
**Method :** `POST`

**URL Params :**
```
action=set-mode
Required
See
Common URL parameters
```

**Data Params :**
```
mechunit={mechunit}
Required
mode={ON|OFF}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mechunit=ROB_1&mode=ON" -X POST "http://localhost/rw/motionsystem/pathsupervision?action=set-mode"
```

---

## Set Path Supervision Level

**Chemin :** RobotWare Services › Motion System › Operations On Path Supervision › Set Path Supervision Level

URL — /rw/motionsystem/pathsupervision

**URL :** `/rw/motionsystem/pathsupervision`  
**Method :** `POST`

**URL Params :**
```
action=set-level
Required
See
Common URL parameters
```

**Data Params :**
```
mechunit={mechunit}
Required
level={level}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mechunit=ROB_1&level=90" -X POST "http://localhost/rw/motionsystem/pathsupervision?action=set-level"
```

---

## Operations On NonMotion Execution

**Chemin :** RobotWare Services › Motion System › Operations On NonMotion Execution

---

## Get Non Motion Execution Mode

**Chemin :** RobotWare Services › Motion System › Operations On NonMotion Execution › Get Non Motion Execution Mode

URL — /rw/motionsystem/nonmotionexecution

**URL :** `/rw/motionsystem/nonmotionexecution`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
mode
{ON|OFF} Nonmotion Execution mode
```

**Success :** HTTP_OK (200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/nonmotionexecution"
```

---

## Get NonMotion Execution Actions

**Chemin :** RobotWare Services › Motion System › Operations On NonMotion Execution › Get NonMotion Execution Actions

URL — /rw/motionsystem/nonmotionexecution

**URL :** `/rw/motionsystem/nonmotionexecution`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
mode
NonMotion Execution mode
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/nonmotionexecution?action=show"
```

---

## Set NonMotion Execution Mode

**Chemin :** RobotWare Services › Motion System › Operations On NonMotion Execution › Set NonMotion Execution Mode

URL — /rw/motionsystem/nonmotionexecution

**URL :** `/rw/motionsystem/nonmotionexecution`  
**Method :** `POST`

**URL Params :**
```
action=set-mode
Required
See
Common URL parameters
```

**Data Params :**
```
mode={ON|OFF}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST (400), FORBIDDEN (403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "mode=ON" -X POST "http://localhost/rw/motionsystem/nonmotionexecution?action=set-mode"
```

---

## Operations on Mechunits

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits

---

## Get Mechunits

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Get Mechunits

URL — /rw/motionsystem/mechunits

**URL :** `/rw/motionsystem/mechunits`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
Gives the information regarding the different mechanical units and the mechanical unit parameters.
title = name of the mechanical unit
mode = {activated | deactivated}
activation-allowed = {true | false} true, if mechanical unit can be activated
drive-module = information if a drive module is associated with the mechanical unit.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits"
```

---

## Operations on Mechunit

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit

---

## Get Mechunit

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Mechunit

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `GET`

**URL Params :**
```
continue-on-err={1|0}
resource={static | dynamic | tool | wobj | payload | total-payload | status | mode | jog-mode | type | task | coord-system | axes | axes-total | is-integrated | has-integrated}
resource parameter value can be given in any combination as mentioned below:
resource=static
resource=static;tool;wobj
resource=static;tool;dynamic
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
resource=static
It gives mechanical unit static(task, type, axes, axes-total, is-integrated, has-integrated) properties info
resource=dynamic
It gives mechanical unit dynamic(tool, wobj, payload, total-payload, status, mode, jog-mode, coord-system) properties info
resource=static;tool;wobj
It gives mechanical unit static, tool and wobj properties info
resource=dynamic;axes;task
It gives mechanical unit dynamic, axes and task properties info
resource=static;dynamic
It gives mechanical unit static and dynamic properties info
continue-on-err=1
It continues the execution even if any error occurs and default value is 0
Returns the details of the mechanical unit under consideration
title = name of the mechanical unit.
tool-name = name of the tool.
wobj-name = work object name.
type = type of the mechanical unit. {None | TCPRobot | Robot | Single | Undefined}
payload-name = name of the payload.
total-payload-name = name for the total payload.
mode = mode of the mechanical unit {activated | deactivated}.
jog-mode = mode of jogging.
axes = number of axes.
axes-total = The total number of axes for the mech unit and possible inegrated units.
coord-system = type of co-ordinate system {World, Base, Tool, Wobj}
status = mechanical unit state.
is-integrated-unit = Name of the mechanical unit which has this mechanical unit as a integrated unit.
has-integrated-unit = Name of the mechanical unit which is integrated with this mechanical unit.
pjoints, robtarget, jointtarget, cartesian, axes are the different resources under mechunit/{mechunit-name} resource. For more information, refer the documentation for the same.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** Not Found(404),BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Sample call1:
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1?continue-on-err=1"
Sample call2:
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1?resource=tool"
Sample call3:
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1?resource=tool;static&continue-on-err=1"
```

---

## Get Mechunit action

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Mechunit action

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `GET`

**URL Params :**
```
action=show
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1?action=show"
```

---

## Set Mechunit

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Set Mechunit

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
continue-on-err={1|0}
See
Common URL parameters
```

**Data Params :**
```
tool={tool_name}
wobj={wobj_name}
payload={payload_name}
total-payload={payload_name}
mode={Activated|Deactivated}
jog-mode={AxisGroup1|AxisGroup2|Align|GoToPos|ConfigurationJog}
coord-system={Wobj|Base|Tool|Word}
At least one data parameter should be provided.
```

**Success :** NO_CONTENT (204): If all APIs are successful
HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "tool=tool1&wobj=wobj2&payload=load2" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1?action=set&continue-on-err=1"
```

---

## Set Compliance Lead Through

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Set Compliance Lead Through

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=set-lead-through
Required
See
Common URL parameters
```

**Data Params :**
```
status={active|inactive}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "status=active" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_R?action=set-lead-through"
```

---

## Get Compliance Lead Through

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Compliance Lead Through

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `GET`

**URL Params :**
```
resource=lead-through
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
status = {active | Inactive}, active if complianceleadthrough functionality is opted for.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1?resource=lead-through"
```

---

## Set Fine Calibration

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Set Fine Calibration

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=fine-calibrate
Required
See
Common URL parameters
```

**Data Params :**
```
axis={axis-value}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "axis=3" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1?action=fine-calibrate"
```

---

## Update (Syncronize) Revolution Counter

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Update (Syncronize) Revolution Counter

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=update-revcounter
Required
See
Common URL parameters
```

**Data Params :**
```
axis={axis-value}
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "axis=3" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1?action=update-revcounter"
```

---

## Get Physical Joints

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Physical Joints

URL — /rw/motionsystem/mechunits/{mechunit}/pjoints

**URL :** `/rw/motionsystem/mechunits/{mechunit}/pjoints`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/pjoints"
```

---

## Get Cartesian Value

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Cartesian Value

URL — /rw/motionsystem/mechunits/{mechunit}/cartesian

**URL :** `/rw/motionsystem/mechunits/{mechunit}/cartesian`  
**Method :** `GET`

**URL Params :**
```
tool={tool_name} By default, active tool configured for the mechunit will be taken.
wobj={wobj_name} By default, active wobj configured for the mechunit will be taken.
coordinate={Base | Word | Tool | Wobj}
Required
elog-at-err={1 | 0} Event log will be generated on error.
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/cartesian?tool=tool0&wobj=wobj1&coordinate=Base&elog-at-err=1"
```

---

## Set Mechanical Unit

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Set Mechanical Unit

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=mechunit-position
Required
See
Common URL parameters
```

**Data Params :**
```
rob_joint=[rob_joint1-value,rob_joint1-value,rob_joint3-value,rob_joint4-value,rob_joint5-value,rob_joint6-value]
Required
ext_joint=[ext_joint1-value,ext_joint2-value,ext_joint3-value,ext_joint4-value,ext_joint5-value,ext_joint6-value]
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "rob_joint=[18.23,8.45,-13.23,-5.25,13.63,-72.31]&ext_joint=[0,0,0,0,0,0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1?action=mechunit-position"
```

---

## Get Robtarget

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Robtarget

URL — /rw/motionsystem/mechunits/{mechunit}/robtarget

**URL :** `/rw/motionsystem/mechunits/{mechunit}/robtarget`  
**Method :** `GET`

**URL Params :**
```
tool={tool_name} By default, active tool configured for the mechunit will be taken.
wobj={wobj_name} By default, active wobj configured for the mechunit will be taken.
coordinate={Base | Word | Tool | Wobj}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/robtarget?tool=tool0&wobj=wobj0&coordinate=Base"
```

---

## Get Joint target

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Joint target

URL — /rw/motionsystem/mechunits/{mechunit}/jointtarget

**URL :** `/rw/motionsystem/mechunits/{mechunit}/jointtarget`  
**Method :** `GET`

**URL Params :**
```
ignore
=1 if present will get joint target always.
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/jointtarget"
```

---

## Subscribe on Mechunit Mode Change

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Subscribe on Mechunit Mode Change

URL — /subscription

**URL :** `/subscription`  
**Method :** `POST`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
resources
=An identifier
Required
*<identifier>*=The subscription resource URI (The URI here is: '/rw/motionsystem/mechunits;mechunitmodechangecount')
Required
*<identifier>-p*=The priority associated with the subscription resource.
Required
```

**Resources :**
```
motionsystem-ev
change-count
Change count
```

**Success :** CREATED(201)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
HTTP Errors, see
HTTP Status codes
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
Subscribe on RAPID task change
only low priority subscription(-p=0) and medium priority subscription(-p=1) are allowed on this resource
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/motionsystem/mechunits;mechunitmodechangecount&1-p=0" "http://localhost/subscription"
curl --digest -u "Default User":robotics -X POST -d "resources=1&1=/rw/motionsystem/mechunits;mechunitmodechangecount&1-p=1" "http://localhost/subscription"
```

**Notes :** Not supported in bootserver mode.

---

## Get Joints From Position

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Joints From Position

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=CalcJointsFromPose
See
Common URL parameters
```

**Data Params :**
```
curr_position = [x,y,z]
Required
curr_ext_joints = [j1,j2,j3,j4,j5,j6]
Required
tool_frame_position = [x, y, z]
Required
curr_orientation = [u0, u1, u2, u3]
Required
tool_frame_orientation = [u0, u1, u2, u3]
Required
old_rob_joints = [j1,j2,j3,j4,j5,j6]
Required
old_ext_joints = [j1,j2,j3,j4,j5,j6]
Required
robot_fixed_object = {TRUE|FALSE}
Required
robot_configuration = [quarter_rev_j1, quarter_rev_j4, quarter_rev_j6, quarter_rev_jx]
Required
elog_at_error = {TRUE|FALSE}
Required
```

**Resources :**
```
robotjoint
Robot joints
extjoint
Robot external joints
```

**Success :** HTTP_OK(200):
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "curr_position=[0.511087716,-0.0101547204,0.665710211]&curr_ext_joints=[0,0,0,0,0,0]&tool_frame_position=[0,0,0]&curr_orientation=[0.184474304,-0.599885881,-0.00642657699,-0.778501570]&tool_frame_orientation=[1.0,0,0,0]&old_rob_joints=[-0.0554263890,0.0185516607,0.151851505,2.56702399,0.540392220,0.813871026]&old_ext_joints=[0,0,0,0,0,0]&robot_fixed_object=FALSE&robot_configuration=[-1,1,0,0]&elog_at_error=FALSE" "http://localhost/rw/motionsystem/mechunits/ROB_1?action=CalcJointsFromPose"
```

---

## Get Position From Joints

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Position From Joints

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=CalcPoseFromJoints
See
Common URL parameters
```

**Data Params :**
```
tool_frame_position = [x, y, z]
Required
tool_frame_orientation = [u0, u1, u2, u3]
Required
rob_joints = [j1,j2,j3,j4,j5,j6]
Required
ext_joints = [j1,j2,j3,j4,j5,j6]
Required
robot_fixed_object = TRUE|FALSE
Required
elog_at_error = TRUE|FALSE
Required
```

**Resources :**
```
position-(x-z)
Current Position
robtargetorientation
Robot Target orientation
robotjoint
Robot joints
extjoint
Robot external joints
quarter_rev_j
Robot configuration
```

**Success :** HTTP_OK(200):
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "tool_frame_position=[0,0,0]&tool_frame_orientation=[1.0,0,0,0]&rob_joints=[-0.0554263890,0.0185516607,0.151851505,2.56702399,0.540392220,0.813871026]&ext_joints=[0,0,0,0,0,0]&robot_fixed_object=FALSE&elog_at_error=FALSE" "http://localhost/rw/motionsystem/mechunits/ROB_1?action=CalcPoseFromJoints"
```

---

## Get All Joint Solution

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get All Joint Solution

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=AllJointSolutions
See
Common URL parameters
```

**Data Params :**
```
curr_position = [x,y,z]
Required
curr_ext_joints = [j1,j2,j3,j4,j5,j6]
Required
tool_frame_position = [x, y, z]
Required
curr_orientation = [u0, u1, u2, u3]
Required
tool_frame_orientation = [u0, u1, u2, u3]
Required
robot_fixed_object = TRUE|FALSE
Required
robot_configuration = [quarter_rev_j1, quarter_rev_j4, quarter_rev_j6, quarter_rev_jx]
Required
```

**Resources :**
```
robotjoint
Robot joints
extjoint
Robot external joints
quarter_rev_j
Robot configuration
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "curr_position=[0.511087716,-0.0101547102,0.665710211]&curr_ext_joints=[0,0,0,0,0,0]&tool_frame_position=[0,0,0]&curr_orientation=[0.675245225,-0.425338209,-0.423074305,-0.429114610]&tool_frame_orientation=[1.0,0,0,0]&robot_fixed_object=FALSE&robot_configuration=[-1,1,1,0]" "http://localhost/rw/motionsystem/mechunits/ROB_R?action=AllJointSolutions"
```

---

## Get Joints From Cartesian

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Joints From Cartesian

URL — /rw/motionsystem/mechunits/{mechunit}

**URL :** `/rw/motionsystem/mechunits/{mechunit}`  
**Method :** `POST`

**URL Params :**
```
action=JointsFromCartesian
See
Common URL parameters
```

**Data Params :**
```
curr_position = [x,y,z]
Required
curr_ext_joints = [j1,j2,j3,j4,j5,j6]
Required
tool_frame_position = [x, y, z]
Required
curr_orientation = [u0, u1, u2, u3]
Required
tool_frame_orientation = [u0, u1, u2, u3]
Required
old_rob_joints = [j1,j2,j3,j4,j5,j6]
Required
old_ext_joints = [j1,j2,j3,j4,j5,j6]
Required
robot_fixed_object = TRUE|FALSE
Required
robot_configuration = [quarter_rev_j1, quarter_rev_j4, quarter_rev_j6, quarter_rev_jx]
Required
elog_at_error = TRUE|FALSE
Required
```

**Resources :**
```
robotjoint
Robot joints
extjoint
Robot external joints
```

**Success :** HTTP_OK(200):
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "curr_position=[0.511087716,-0.0101547204,0.665710211]&curr_ext_joints=[0,0,0,0,0,0]&tool_frame_position=[0,0,0]&curr_orientation=[0.184474304,-0.599885881,-0.00642657699,-0.778501570]&tool_frame_orientation=[1.0,0,0,0]&old_rob_joints=[-0.0554263890,0.0185516607,0.151851505,2.56702399,0.540392220,0.813871026]&old_ext_joints=[0,0,0,0,0,0]&robot_fixed_object=FALSE&robot_configuration=[-1,1,0,0]&elog_at_error=FALSE" "http://localhost/rw/motionsystem/mechunits/ROB_1?action=JointsFromCartesian"
```

---

## Get Calibration Info

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Get Calibration Info

URL — /rw/motionsystem/mechunits/{mechunit}/calibrationinfo

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calibrationinfo`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
usecalibrationwindowtype
calibration window count
noactivejoints
number of active joints
count
total count
calibrationmethodused
name of calibration method
showaxis
axis present or not {1|0}
jointname
name of joint
factorycalibrationmethod
factory calibration method name
currentcalibrationmethod
current calibration method name
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/calibrationinfo"
```

---

## Operation on Calib

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib

---

## Calibration for BaseFrame

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for BaseFrame

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=BaseFrame
Required
type=ROBOT
Required
reference=[x, y, z]
Required
point1=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point2=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point3=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point4=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point5=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point6=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point7=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point8=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point9=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
point10=[x, y, z, q1, q2, q3, q4, j1, j4, j6, jx]
At least 3 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=BaseFrame&type=ROBOT&reference=[0,0,0]&point1=[349.9289,7.176809,509.6597,0.5466173,-0.008585534,0.8373197,0.005604791,0,0,0,0]&point2=[285.9633,106.211,689.8639,0.7294637,-0.1187442,0.6607552,0.1310918,0,0,0,0]&point3=[269.1732,143.5324,689.8639,0.7190274,-0.1627988,0.6513019,0.1797274,0,0,0,0]&point4=[270.8943,144.4501,659.9161,0.6966563,-0.1687667,0.6751775,0.1741356,0,0,0,0]&point5=[304.7093,37.4411,659.9161,0.7167487,-0.04251764,0.6946503,0.04387021,0,0,0,0]&point6=[229.2431,28.16821,705.6543,0.7913748,-0.0372306,0.6082709,0.04843788,0,0,0,0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for BaseFrameMoving

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for BaseFrameMoving

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=BaseFrameMoving
Required
type=ROBOT2
Required
point1=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point2=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point3=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point4=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point5=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point6=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point7=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point8=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point9=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
point10=[x, y, z, q1, q2, q3, q4, x2, y2, z2, q2_1, q2_2, q2_3, q2_4, j1, j4, j6, jx]
At least 3 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST (400) ,See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=BaseFrameMoving&type=ROBOT2&point1=[0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1]&point2=[0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1]&point3=[0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for ExternalRobotNomBaseNew

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for ExternalRobotNomBaseNew

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=ExternalRobotNomBaseNew
Required
type=SINGLE
Required
point1=[x, y, z, q1, q2, q3, q4, axis_value]
point2=[x, y, z, q1, q2, q3, q4, axis_value]
point3=[x, y, z, q1, q2, q3, q4, axis_value]
point4=[x, y, z, q1, q2, q3, q4, axis_value]
point5=[x, y, z, q1, q2, q3, q4, axis_value]
point6=[x, y, z, q1, q2, q3, q4, axis_value]
point7=[x, y, z, q1, q2, q3, q4, axis_value]
point8=[x, y, z, q1, q2, q3, q4, axis_value]
point9=[x, y, z, q1, q2, q3, q4, axis_value]
point10=[x, y, z, q1, q2, q3, q4, axis_value]
At least 3 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=ExternalRobotNomBaseNew&type=SINGLE&point1=[0, 0, 0, 1, 0, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0, 0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for RobotAxisRot

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for RobotAxisRot

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=RobotAxisRot
Required
type=SINGLE
Required
tolerance={tolerance_value}
Required
axis={axis_num}
Required
point1=[x, y, z, q1, q2, q3, q4, axis_value]
point2=[x, y, z, q1, q2, q3, q4, axis_value]
point3=[x, y, z, q1, q2, q3, q4, axis_value]
point4=[x, y, z, q1, q2, q3, q4, axis_value]
point5=[x, y, z, q1, q2, q3, q4, axis_value]
point6=[x, y, z, q1, q2, q3, q4, axis_value]
point7=[x, y, z, q1, q2, q3, q4, axis_value]
point8=[x, y, z, q1, q2, q3, q4, axis_value]
point9=[x, y, z, q1, q2, q3, q4, axis_value]
point10=[x, y, z, q1, q2, q3, q4, axis_value]
At least 4 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=RobotAxisRot&type=SINGLE&tolerance=0&axis=0&point1=[0, 0, 0, 1, 0, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0, 0]&point4=[0, 0, 0, 1, 0, 0, 0, 0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for SingleUserRotNew

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for SingleUserRotNew

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=SingleUserRotNew
Required
type=SINGLE
Required
tolerance={tolerance_value}
Required
point1=[x, y, z, q1, q2, q3, q4, axis_value]
point2=[x, y, z, q1, q2, q3, q4, axis_value]
point3=[x, y, z, q1, q2, q3, q4, axis_value]
point4=[x, y, z, q1, q2, q3, q4, axis_value]
point5=[x, y, z, q1, q2, q3, q4, axis_value]
point6=[x, y, z, q1, q2, q3, q4, axis_value]
point7=[x, y, z, q1, q2, q3, q4, axis_value]
point8=[x, y, z, q1, q2, q3, q4, axis_value]
point9=[x, y, z, q1, q2, q3, q4, axis_value]
point10=[x, y, z, q1, q2, q3, q4, axis_value]
At least 4 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400) ,See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=SingleUserRotNew&type=SINGLE&tolerance=0&point1=[0, 0, 0, 1, 0, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0, 0]&point4=[0, 0, 0, 1, 0, 0, 0, 0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for RotExtCtrlZdef

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for RotExtCtrlZdef

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=RotExtCtrlZdef
Required
type=SINGLE
Required
tolerance={tolerance_value}
Required
pose=[x, y, z, q1, q2, q3, q4]
Required
point1=[x, y, z, q1, q2, q3, q4, axis_value]
point2=[x, y, z, q1, q2, q3, q4, axis_value]
point3=[x, y, z, q1, q2, q3, q4, axis_value]
point4=[x, y, z, q1, q2, q3, q4, axis_value]
point5=[x, y, z, q1, q2, q3, q4, axis_value]
point6=[x, y, z, q1, q2, q3, q4, axis_value]
point7=[x, y, z, q1, q2, q3, q4, axis_value]
point8=[x, y, z, q1, q2, q3, q4, axis_value]
point9=[x, y, z, q1, q2, q3, q4, axis_value]
point10=[x, y, z, q1, q2, q3, q4, axis_value]
At least 4 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=RotExtCtrlZdef&type=SINGLE&tolerance=1&pose=[0, 0, 0, 0, 1, 0, 0]&point1=[0, 0, 0, 1, 0, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0, 0]&point4=[0, 0, 0, 1, 0, 0, 0, 0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for SingleUserLin

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for SingleUserLin

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=SingleUserLin
Required
type=SINGLE
Required
tolerance={tolerance_value}
Required
point1=[x, y, z, q1, q2, q3, q4, axis_value]
point2=[x, y, z, q1, q2, q3, q4, axis_value]
point3=[x, y, z, q1, q2, q3, q4, axis_value]
point4=[x, y, z, q1, q2, q3, q4, axis_value]
point5=[x, y, z, q1, q2, q3, q4, axis_value]
point6=[x, y, z, q1, q2, q3, q4, axis_value]
point7=[x, y, z, q1, q2, q3, q4, axis_value]
point8=[x, y, z, q1, q2, q3, q4, axis_value]
point9=[x, y, z, q1, q2, q3, q4, axis_value]
point10=[x, y, z, q1, q2, q3, q4, axis_value]
At least 3 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400) ,See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=SingleUserLin&type=SINGLE&tolerance=0&point1=[0, 0, 0, 1, 0, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0, 0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for SingleTrack

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for SingleTrack

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=SingleTrack
Required
type=SINGLE
Required
point1=[x, y, z, q1, q2, q3, q4, axis_value]
point2=[x, y, z, q1, q2, q3, q4, axis_value]
point3=[x, y, z, q1, q2, q3, q4, axis_value]
point4=[x, y, z, q1, q2, q3, q4, axis_value]
point5=[x, y, z, q1, q2, q3, q4, axis_value]
point6=[x, y, z, q1, q2, q3, q4, axis_value]
point7=[x, y, z, q1, q2, q3, q4, axis_value]
point8=[x, y, z, q1, q2, q3, q4, axis_value]
point9=[x, y, z, q1, q2, q3, q4, axis_value]
point10=[x, y, z, q1, q2, q3, q4, axis_value]
At least 3 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST (400) ,See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=SingleTrack&type=SINGLE&point1=[0, 0, 0, 1, 0, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0, 0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Calibration for RobotAxisRot2

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operation on Calib › Calibration for RobotAxisRot2

URL — /rw/motionsystem/mechunits/{mechunit}/calib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/calib`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
method=RobotAxisRot2
Required
type=SINGLE2
Required
tolerance={tolerance_value}
Required
axis={axis_num}
Required
point1=[x, y, z, q1, q2, q3, q4, axis_value]
point2=[x, y, z, q1, q2, q3, q4, axis_value]
point3=[x, y, z, q1, q2, q3, q4, axis_value]
point4=[x, y, z, q1, q2, q3, q4, axis_value]
point5=[x, y, z, q1, q2, q3, q4, axis_value]
point6=[x, y, z, q1, q2, q3, q4, axis_value]
point7=[x, y, z, q1, q2, q3, q4, axis_value]
point8=[x, y, z, q1, q2, q3, q4, axis_value]
point9=[x, y, z, q1, q2, q3, q4, axis_value]
point10=[x, y, z, q1, q2, q3, q4, axis_value]
At least 4 points are required.
```

**Resources :**
```
x, y, z
Represents base frame position
q1, q2, q3, q4
Represents base frame orientation
max-err
Represents the maximum error for one positioning
min-err
Represents the minimum error for one positioning
mean-err
Represents the accuracy of the robot positioning against the tip
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "method=RobotAxisRot2&type=SINGLE2&tolerance=0&axis=0&point1=[0, 0, 0, 1, 0, 0, 0, 0]&point2=[0, 0, 0, 1, 0, 0, 0, 0]&point3=[0, 0, 0, 1, 0, 0, 0, 0]&point4=[0, 0, 0, 1, 0, 0, 0, 0]" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/calib"
```

---

## Operations on Baseframe

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Baseframe

---

## Get Base Frame

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Baseframe › Get Base Frame

URL — /rw/motionsystem/mechunits/{mechunit}/baseframe

**URL :** `/rw/motionsystem/mechunits/{mechunit}/baseframe`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400), UNSUPPORTED_MEDIA(415)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/baseframe"
```

---

## Get Base Frame actions

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Baseframe › Get Base Frame actions

URL — /rw/motionsystem/mechunits/{mechunit}/baseframe

**URL :** `/rw/motionsystem/mechunits/{mechunit}/baseframe`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/baseframe?action=show"
```

---

## Set Base Frame

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Baseframe › Set Base Frame

URL — /rw/motionsystem/mechunits/{mechunit}/baseframe

**URL :** `/rw/motionsystem/mechunits/{mechunit}/baseframe`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
See
Common URL parameters
```

**Data Params :**
```
x={x-cordinate}
y={y-cordinate}
z={z-cordinate}
q1={quaternion angle 1}
q2={quaternion angle 2}
q3={quaternion angle 3}
q4={quaternion angle 4}
```

**Success :** ACCEPTED(202)
see
HTTP Status codes

**Error :** BAD_REQUEST(400), Forbidden(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "x=1&y=2&z=3&q1=0.1825742&q2=0.3651484&q3=0.5477226&q4=0.7302967" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/baseframe?action=set"
```

---

## Operations on Axes

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes

---

## Get Axes

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes › Get Axes

URL — /rw/motionsystem/mechunits/{mechunit}/axes

**URL :** `/rw/motionsystem/mechunits/{mechunit}/axes`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
This API provides the number of joints of the mechanical unit under consideration.
title = axes, provides the number of joints on the mechanical unit.
title = axis, provides the details of the specific joint in the mechanical unit.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/axes"
```

---

## Get Axis

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes › Get Axis

URL — /rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}

**URL :** `/rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Resources :**
```
This API provides the details of the specific axis of the mechanical unit.
axisstatus
: mechanical unit axis state.Possible values are,
Initiated-State is initialted.
NotCommutated-State is not commutated.
NotCalibrated-State is not calibrated
NotAMSSynchronized-One or several absolute measurement axes are not synchronized.
NotSMSSynchronized-One or several relative measurement axes are not synchronized.
Synchronized-State is synchronized.
Locked-State is locked.
LockedShow-State locked show
Undefined
axispose
: Axis number.
logicalaxis
: The logical joint number of the mechanical unit axis.
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/axes/1"
```

---

## Get Axis actions

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes › Get Axis actions

URL — /rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}

**URL :** `/rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
x, y, z = 3D co-ordinates of the position of the mechanical unit.
q1, q2, q3, q4 = angles of rotation
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://http://localhost/rw/motionsystem/mechunits/ROB_1/axes/1?action=show
"
```

---

## Get Axis pose

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes › Get Axis pose

URL — /rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}

**URL :** `/rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}`  
**Method :** `GET`

**URL Params :**
```
resource=axis-pose
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
x, y, z
Represents axis pose position
q1, q2, q3, q4
Represents axis pose orientation
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/axes/1?resource=axis-pose"
```

---

## Set Axis pose

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes › Set Axis pose

URL — /rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}

**URL :** `/rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}`  
**Method :** `POST`

**URL Params :**
```
action=set-axispose
Required
See
Common URL parameters
```

**Data Params :**
```
x={x_position}
y={y_position}
z={z_position}
q1={q1_value}
q2={q2_value}
q3={q3_value}
q4={q4_value}
```

**Success :** NO_CONTENT (204), see
HTTP Status codes

**Error :** BAD_REQUEST(400), NOT_FOUND(404), FORBIDDEN(403)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "x=0&y=0&z=0&q1=0&q2=1&q3=0&q4=0" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/axes/1?action=set-axispose"
```

---

## Update Commutate

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes › Update Commutate

URL — /rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}

**URL :** `/rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}`  
**Method :** `POST`

**URL Params :**
```
action=update-commutate
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics" "
http://localhost/rw/motionsystem/mechunits/ROB_1/axes/1?action=update-commutate
"
```

---

## Update Sync Revolution Counter

**Chemin :** RobotWare Services › Motion System › Operations on Mechunits › Operations on Mechunit › Operations on Axes › Update Sync Revolution Counter

URL — /rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}

**URL :** `/rw/motionsystem/mechunits/{mechunit}/axes/{axis_num}`  
**Method :** `POST`

**URL Params :**
```
action=update-syncrevcounter
Required
See
Common URL parameters
```

**Data Params :**
```
syncType=1
Required
```

**Success :** NO_CONTENT (204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "syncType=1" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/axes/1?action=update-syncrevcounter"
```

---

## Operations on SMB Data

**Chemin :** RobotWare Services › Motion System › Operations on SMB Data

---

## Set SMB Data

**Chemin :** RobotWare Services › Motion System › Operations on SMB Data › Set SMB Data

URL — /rw/motionsystem/mechunits/{mechunit}/smbdata

**URL :** `/rw/motionsystem/mechunits/{mechunit}/smbdata`  
**Method :** `POST`

**URL Params :**
```
action=set
Required
See
Common URL parameters
```

**Data Params :**
```
type=robot-to-controller | controller-to-robot
```

**Success :** NO_CONTENT (204) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "type=robot-to-controller" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/smbdata?action=set"
```

---

## Clear SMB Data

**Chemin :** RobotWare Services › Motion System › Operations on SMB Data › Clear SMB Data

URL — /rw/motionsystem/mechunits/{mechunit}/smbdata

**URL :** `/rw/motionsystem/mechunits/{mechunit}/smbdata`  
**Method :** `POST`

**URL Params :**
```
action=clear
Required
See
Common URL parameters
```

**Data Params :**
```
type={robot|controller}
```

**Success :** NO_CONTENT (204) see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "type=robot" -X POST "http://localhost/rw/motionsystem/mechunits/ROB_1/smbdata?action=clear"
```

---

## Get SMB Data

**Chemin :** RobotWare Services › Motion System › Operations on SMB Data › Get SMB Data

URL — /rw/motionsystem/mechunits/{mechunit}/smbdata

**URL :** `/rw/motionsystem/mechunits/{mechunit}/smbdata`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
cabinet_sis_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
cabinet_abs_acc_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
cabinet_calib_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
sensor_memory_sis_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
sensor_memory_abs_acc_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
sensor_memory_calib_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
cabinet_axis_cal_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
sensor_memory_axis_cal_data_status
= {0|1|2|3}, where 0 is SMB_VALID, 1 is SMB_VALID_NOT_EQUAL, 2 is SMB_NOT_VALID and 3 is SMB_NOT_USED
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/smbdata"
```

---

## Get SMB Data Actions

**Chemin :** RobotWare Services › Motion System › Operations on SMB Data › Get SMB Data Actions

URL — /rw/motionsystem/mechunits/{mechunit}/smbdata

**URL :** `/rw/motionsystem/mechunits/{mechunit}/smbdata`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/smbdata?action=show"
```

---

## Operations on Motor Calib

**Chemin :** RobotWare Services › Motion System › Operations on Motor Calib

---

## Get Motor Calib Names

**Chemin :** RobotWare Services › Motion System › Operations on Motor Calib › Get Motor Calib Names

URL — /rw/motionsystem/mechunits/{mechunit}/motorcalib

**URL :** `/rw/motionsystem/mechunits/{mechunit}/motorcalib`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200), see
HTTP Status codes

**Error :** NOT_FOUND(404), BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/motionsystem/mechunits/ROB_1/motorcalib"
```

---

## Integrated Vision (IV) Service

**Chemin :** RobotWare Services › Integrated Vision (IV) Service

---

## Get Vision Manager Resource

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get Vision Manager Resource

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** NOT_FOUND(404)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision"
```

**Notes :** Not supported in bootserver mode

---

## Get Number of Cameras of IV

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get Number of Cameras of IV

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
resource=num-of-cameras
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
number-of-cameras:
Number of cameras present in Integrated Vision Device
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision?resource=num-of-cameras"
```

**Notes :** Not supported in bootserver mode

---

## Get IV Camera Validity

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get IV Camera Validity

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
resource=camera-validity
Required
name={camera-name}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
is-valid-camera-name:
Given camera Name is valid or not
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision?resource=camera-validity&name=camera1"
```

**Notes :** Not supported in bootserver mode

---

## Get Vision (camera) Resource Actions

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get Vision (camera) Resource Actions

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
action=show
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
restart:
Restart the Camera.
flash-led:
Flash the LED(s) of the Camera.
set-state:
Set the state of the camera. {state = standby | run}
refresh:
Refresh the cameras
set-hostname:
Set the hostname for the camera.
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision?action=show"
```

**Notes :** Not supported in bootserver mode

---

## Get Camera Jobname

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get Camera Jobname

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
resource=camera-job
Required
name={camera-name}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
jobname:
name of the job on the camera
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision?resource=camera-job&name=mycamera"
```

**Notes :** Not supported in bootserver mode

---

## Restart Camera

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Restart Camera

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=restart
Required
```

**Data Params :**
```
name={camera-name}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=mycamera" -X POST "http://localhost/rw/vision?action=restart"
```

**Notes :** Not supported in bootserver mode

---

## Flash LED(s) of Camera

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Flash LED(s) of Camera

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=flash-led
Required
```

**Data Params :**
```
name={camera-name}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=mycamera" -X POST "http://localhost/rw/vision?action=flash-led"
```

**Notes :** Not supported in bootserver mode

---

## Set Camera State

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Set Camera State

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=set-state
Required
```

**Data Params :**
```
name={camera-name}
Required
state={standby | run}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=mycamera&state=run" -X POST "http://localhost/rw/vision?action=set-state"
```

**Notes :** Not supported in bootserver mode

---

## Refesh the camera(s)

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Refesh the camera(s)

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=refresh
Required
```

**Data Params :**
```
None
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X POST "http://localhost/rw/vision?action=refresh"
```

**Notes :** Not supported in bootserver mode

---

## Set Hostname of the Camera

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Set Hostname of the Camera

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=set-hostname
Required
```

**Data Params :**
```
name={camera-name}
Required
host={host-name}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=mycamera&host=hostname" -X POST "http://localhost/rw/vision?action=set-hostname"
```

**Notes :** A restart for the camera module is needed for the change to be visible. Switch Off and switch On the camera modeule.
Not supported in bootserver mode

---

## Set camera to be a DHCP client

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Set camera to be a DHCP client

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=set-dhcp
Required
```

**Data Params :**
```
name={camera-name}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400),FORBIDDEN(403),NOT_FOUND(404)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=mycamera" -X POST "http://localhost/rw/vision?action=set-dhcp"
```

**Notes :** Not supported in bootserver mode
Camera restart is required after DHCP settings

---

## Set Camera DNS Settings

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Set Camera DNS Settings

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=set-dns-settings
Required
```

**Data Params :**
```
name={camera-name}
Required
dns-server={dns-server-value}
Required
dns-suffix={dns-suffix-name}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400),FORBIDDEN(403),NOT_FOUND(404)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "name=mycamera&dns-server=192.168.125.76&dns-suffix=yourdomain.com" -X POST "http://localhost/rw/vision?action=set-dns-settings"
```

**Notes :** Not supported in bootserver mode
Camera restart is required after DNS settings

---

## Get Camera Status

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get Camera Status

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
resource=camera-status
Required
name={camera-name}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
camera-status:
status of the camera {Disconnected | Program | Running | Unconfigured}
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision?resource=camera-status&name=mycamera"
```

**Notes :** Not supported in bootserver mode

---

## Get Camera Info Using Index of the camera

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get Camera Info Using Index of the camera

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
resource=camera-info-index
Required
index={camera index}
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
camera-info-using-index:
Gives all information about camera
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision?resource=camera-info-index&index=0"
```

**Notes :** Not supported in bootserver mode

---

## Set Camera Name

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Set Camera Name

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=set-cameraname
Required
```

**Data Params :**
```
index={camera-index}
Required
name={cameraname}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
FORBIDDEN(403)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "index=0&name=mycamera" -X POST "http://localhost/rw/vision?action=set-cameraname"
```

**Notes :** Not supported in bootserver mode
Restart the controller to aplly changes

---

## Set Camera User Credentials

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Set Camera User Credentials

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=set-user-credential
Required
```

**Data Params :**
```
index={camera-index}
Required
user={user name}
Required
password={password}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "index=0&user=cmycamera&password=123" -X POST "http://localhost/rw/vision?action=set-user-credential"
```

**Notes :** Not supported in bootserver mode
Restart is required to be activated

---

## Set Camera IP Settings

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Set Camera IP Settings

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `POST`

**URL Params :**
```
action=set-ip-settings
Required
```

**Data Params :**
```
name={cameraname}
Required
address={ip-address}
Required
netmask={subnetmask-value}
Required
gateway={gateway value}
Required
```

**Success :** NO_CONTENT(204)
see
HTTP Status codes

**Error :** BAD_REQUEST(400),FORBIDDEN(403),NOT_FOUND(404)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics-d "name=mycamera&address=192.168.125.206&netmask=255.255.255.0&gateway=0.0.0.0" -X POST "http://localhost/rw/vision?action=set-ip-settings"
```

**Notes :** Not supported in bootserver mode.
Restart the controller to apply IP settings.

---

## Get IV Camera Info

**Chemin :** RobotWare Services › Integrated Vision (IV) Service › Get IV Camera Info

URL — /rw/vision

**URL :** `/rw/vision`  
**Method :** `GET`

**URL Params :**
```
resource=camera-info
Required
name = {camera-name}
Required
```

**Data Params :**
```
None
```

**Resources :**
```
camera-info:
Gives all information about camera
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** BAD_REQUEST(400)
Robot controller errors, see
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/vision?resource=camera-info&name=myCamera"
```

**Notes :** Not supported in bootserver mode

---

## Operations on IO Profinet Device

**Chemin :** Operations on IO Profinet Device

---

## Get profinet I/O device read record implicit data from device in profinet network

**Chemin :** Operations on IO Profinet Device › Get profinet I/O device read record implicit data from device in profinet network

URL — rw/iosystem/devices/{network}/{device}/implicitdata

**URL :** `rw/iosystem/devices/{network}/{device}/implicitdata`  
**Method :** `GET`

**URL Params :**
```
slot = Device slot number
Required
subslot = Device sub module slot number
Required
index = Represents the read record index according to profinet specifications
Required
datalength = Represents the maximum amount of data in bytes to be read. If the payload for the requested index is larger than specified DataLength the request will return error.
Required
vendorid = Device Vendor ID according GSDML file or DCP identify
Required
deviceid = Device ID according GSDML file or DCP identify
Required
ip = Profinet device IP Address
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
see
HTTP Status codes

**Error :** Bad Request(406)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices/{profinet}/{pnet}/implicitdata"
```

**Notes :** Not supported in bootserver mode.

---

## Read record implicit data from device in profinet network

**Chemin :** Operations on IO Profinet Device › Read record implicit data from device in profinet network

URL — rw/iosystem/devices/{network}/{device}/implicitdata

**URL :** `rw/iosystem/devices/{network}/{device}/implicitdata`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
slot = Device slot number
Required
subslot = Device sub module slot number
Required
index = Represents the read record index according to profinet specifications
Required
datalength = Represents the maximum amount of data in bytes to be read. If the payload for the requested index is larger than specified DataLength the request will return error.
Required
vendorid = Device Vendor ID according GSDML file or DCP identify
Required
deviceid = Device ID according GSDML file or DCP identify
Required
ip = Profinet device IP Address
Required
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** NOT_ACCEPTABLE(406)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "slot=1&subslot=2&index=2&datalength=60&vendorid=42&deviceid=787&ip=127.1.1.0" -X POST "http://localhost/rw/iosystem/devices/{profinet}/{pnet}/implicitdata"
```

**Notes :** Not supported in bootserver mode.

---

## Get forms

**Chemin :** Operations on IO Profinet Device › Get forms

URL — rw/iosystem/devices/{network}/{device}/implicitdata

**URL :** `rw/iosystem/devices/{network}/{device}/implicitdata`  
**Method :** `OPTIONS`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Actions :**
```
None
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** NOT_ACCEPTABLE(406) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X OPTIONS "http://localhost/rw/iosystem/devices/PROFINET/PN_Internal_Device/implicitdata"
```

**Notes :** Not supported in bootserver mode.

---

## Get profinet I/O device read record data

**Chemin :** Operations on IO Profinet Device › Get profinet I/O device read record data

URL — rw/iosystem/devices/{network}/{device}/explicitdata

**URL :** `rw/iosystem/devices/{network}/{device}/explicitdata`  
**Method :** `GET`

**URL Params :**
```
slot = Device slot number
Required
subslot = Device sub module slot number
Required
index = Represents the read record index according to PROFINET specifications
Required
datalength = Represents the maximum amount of data in bytes to be read. If the payload for the requested index is larger than specified DataLength the request will return error.
Required
See
Common URL parameters
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** NOT_ACCEPTABLE(406)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices/PROFINET/PN_Internal_Device/explicitdata"
```

**Notes :** Not supported in bootserver mode

---

## Get profinet I/O device read record data

**Chemin :** Operations on IO Profinet Device › Get profinet I/O device read record data

URL — rw/iosystem/devices/{network}/{device}/explicitdata

**URL :** `rw/iosystem/devices/{network}/{device}/explicitdata`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
slot = Device slot number
Required
subslot = Device sub module slot number
Required
index = Represents the read record index according to PROFINET specifications
Required
datalength = Represents the maximum amount of data in bytes to be read. If the payload for the requested index is larger than specified DataLength the request will return error.
Required
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** NOT_ACCEPTABLE(406)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d "slot=1&subslot=2&index=2&datalength=60" -X POST "http://localhost/rw/iosystem/devices/PROFINET/PN_Internal_Device/explicitdata"
```

**Notes :** Not supported in bootserver mode.

---

## Get Forms

**Chemin :** Operations on IO Profinet Device › Get Forms

URL — rw/iosystem/devices/{network}/{device}/explicitdata

**URL :** `rw/iosystem/devices/{network}/{device}/explicitdata`  
**Method :** `OPTIONS`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Actions :**
```
None
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X OPTIONS "http://localhost/rw/iosystem/devices/PROFINET/PN_Internal_Device/explicitdata"
```

**Notes :** Not supported in bootserver mode.

---

## Get profinet device alarms xml response

**Chemin :** Operations on IO Profinet Device › Get profinet device alarms xml response

URL — rw/iosystem/devices/{network}/{device}/alarms

**URL :** `rw/iosystem/devices/{network}/{device}/alarms`  
**Method :** `GET`

**URL Params :**
```
None
See
Common URL parameters
```

**Data Params :**
```
None
```

**Resources :**
```
nrofretrievedalarms
Total number of received PROFINET alarms since system start.
alarmtype
Type of alarm The alarm type according to PROFINET Protocol Specification
moduleid
The identification number of the PROFINET module for which the alarm is reported.
sub-moduleid
The identification number of the PROFINET submodule for which the alarm is reported.
slot-number
The device slot number in which the reporting module is used.
sub-slot-number
The module slot number in which the reporting submodule is used.
alarm-specifier
Alarm specifier according to PROFINET specification. Contains various parameters for the reported alarm.
usi
UserStructureIdentifier. This parameter identifies the structure of the field Data of the AlarmNotification and the structure of the field Data within the alarm data. It is used for the distinction of ChannelDiagnosis, ExtChannelDiagnosis, QualifiedChannelDiagnosis, and manufacturer specific diagnosis.
maintenance-status
MaintenanceStatus according to PROFINET Specification.
channel-number
The channel number id of the diagnostics source.
channel-props
ChannelProperties according to PROFINET Specification. Consists information about the channel that the alarm is reported for, such as direction and severity etc.
channel-number
ChannelErrorType according to PROFINET Specification. This parameter represents the main error type of the channel related diagnosis..
ext-channel-errtype
ExtChannelErrorType according to PROFINET Specification. This parameter transports the extended error type which is bound to the parameter ChannelErrorType..
ext-channel-add-value
ExtChannelAddValue according to PROFINET Specification. This parameter contains an additional value in case of extended channel diagnosis.
channel-qualifier
QualifiedChannelQualifier according to PROFINET Specification. Describes the severity according to the extended severity scheme.
alarm-payload-len
The length of the reported alarm payload (bytes).
time-sec
Current time in UNIX time format in seconds. Number of seconds that have elapsed since January 1st, 1970 00:00:00 UTC.
time-ms
Microseconds lapsed for each seconds.
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** NOT_ACCEPTABLE(406)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics "http://localhost/rw/iosystem/devices/PROFINET/PN_Internal_Device/alarms"
```

**Notes :** Not supported in bootserver mode

---

## Clear the alarms

**Chemin :** Operations on IO Profinet Device › Clear the alarms

URL — rw/iosystem/devices/{network}/{device}/alarms/clear

**URL :** `rw/iosystem/devices/{network}/{device}/alarms/clear`  
**Method :** `POST`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Success :** HTTP_OK(20)
See
HTTP Status codes

**Error :** NOT_ACCEPTABLE(406)
See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -d POST "http://localhost/rw/iosystem/devices/PROFINET/PN_Internal_Device/alarms/clear"
```

**Notes :** Not supported in bootserver mode.

---

## Get Forms

**Chemin :** Operations on IO Profinet Device › Get Forms

URL — rw/iosystem/devices/{network}/{device}/alarms/clear

**URL :** `rw/iosystem/devices/{network}/{device}/alarms/clear`  
**Method :** `OPTIONS`

**URL Params :**
```
None
```

**Data Params :**
```
None
```

**Actions :**
```
None
```

**Success :** HTTP_OK(200)
See
HTTP Status codes

**Error :** NOT_ACCEPTABLE(406) See
Robot controller return codes

**Sample Call :**
```bash
curl --digest -u "Default User":robotics -X OPTIONS "http://localhost/rw/iosystem/devices/PROFINET/PN_Internal_Device/alarms/clear"
```

**Notes :** Not supported in bootserver mode.

---

