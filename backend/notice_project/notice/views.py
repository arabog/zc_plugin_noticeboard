import requests
import json
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .email import subscription_success_mail
from .schedulestorage import schDb
from .serializers import (
    BookmarkNoticeSerializer,
    CreateNoticeSerializer,
    DraftSerializer,
    NoticeboardRoom,
    NoticeReminderSerializer,
    SchedulesSerializer,
    SubscribeSerializer,
    InstallSerializer,
    UninstallSerializer    
    # UnsubscribeSerializer,
)
from .storage import db
from .utils import user_rooms

# this is a comment


@api_view(["GET"])
def sidebar_info(request):
    """Returns the room the logged in user belongs to under Noticeboard
    plugin"""
    org_id = request.GET.get("org")
    user_id = request.GET.get("user")

    data = {
        "title": "Noticeboard",
        "icon": (
            "https://media.istockphoto.com/vectors/notice-paper-with-push-pin-icon-in-"
            "trendy-flat-design-vector-id1219927783?k=20&m=1219927783&s=612x612&w=0&h="
            "DJ9N_kyvpqh11qHOcD0EZVbM0NeBNC_08oViRjo7G7c="
        ),
        "action": "open",
    }

    room = db.read("noticeboard_room", org_id)

    if room["status"] == 200:
        if room["data"]:
            room = room["data"][0]
        else:
            requests.post(
                f"https://noticeboard.zuri.chat/api/v1/organisation/{org_id}/create-room",
                data=data,
            )
            # room = requests.post(f"http://localhost:8000/api/v1/organisation/{org_id}/create-room", data=data)
    else:
        requests.post(
            f"https://noticeboard.zuri.chat/api/v1/organisation/{org_id}/create-room",
            data=data,
        )
        # room = requests.post(f"http://localhost:8000/api/v1/organisation/{org_id}/create-room", data=data)

    if org_id and user_id:
        sidebar = {
            "name": "Noticeboard Plugin",
            "description": "Displays Information On A Noticeboard",
            "plugin_id": settings.PLUGIN_ID,
            "organisation_id": f"{org_id}",
            "user_id": f"{user_id}",
            "group_name": "Noticeboard",
            "show_group": False,
            "public_rooms": [],
            "joined_rooms": user_rooms(org_id, user_id),
        }
        return Response(sidebar)
    return Response(
        {"message": "org id or user id is None"}, status=status.HTTP_400_BAD_REQUEST
    )

@api_view(["POST"])
def install(request):
    """This endpoint is called when an organisation wants to install the
    Noticeboard plugin for their workspace."""
    serializer = InstallSerializer(data=request.data)
    if serializer.is_valid():    
        install_payload= serializer.data
        org_id=install_payload["organisation_id"]
        user_id=install_payload["user_id"]
        print(org_id,user_id)

        new_token= db.token()
        print(new_token) 

        url=f"https://api.zuri.chat/organizations/{org_id}/plugins"
        print(url)
        payload = {"plugin_id": "613fc3ea6173056af01b4b3e","user_id":user_id}
        v2load=json.dumps(payload).encode("utf-8")
        headers = {'Authorization':f'Bearer {new_token}'}
        response = requests.request("POST", url, headers=headers, data=v2load)
        installed=json.loads(response.text)
        print(installed)
        if installed["status"] == 200:
            return Response({"success": True,"data": {"redirect_url":"/noticeboard"},
                        "message": "sucessfully retrieved",},status=status.HTTP_200_OK,)
        return Response({"Plugin has already been added"},status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors,status=status.HTTP_404_NOT_FOUND)

@api_view(["DELETE"])    
def uninstall(request):
    """This endpoint is called when an organisation wants to uinstall the
    Noticeboard plugin for their workspace."""
    serializer = UninstallSerializer(data=request.data)
    if serializer.is_valid():    
        uninstall_payload= serializer.data
        org_id=uninstall_payload["organisation_id"]
        user_id=uninstall_payload["user_id"]
        print(user_id)

        new_token= db.token()
        print(new_token) 

        url=f"https://api.zuri.chat/organizations/{org_id}/plugins/613fc3ea6173056af01b4b3e"
        print(url)
        payload = {"user_id":user_id}
        v2load=json.dumps(payload).encode("utf-8")
        headers = {'Authorization':f'Bearer {new_token}'}
        response = requests.request("DELETE", url, headers=headers, data=v2load)
        uninstalled=json.loads(response.text)
        print(uninstalled)
        if uninstalled["status"] == 200:
            return Response(uninstalled,status=status.HTTP_200_OK,)
        return Response({"message":"Plugin does not exist"},status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors,status=status.HTTP_404_NOT_FOUND)



@api_view(["POST"])
def create_room(request, org_id):
    """Creates a room for the organisation under Noticeboard plugin."""
    # org_id = "6145b49e285e4a18402073bc"
    # org_id = "614679ee1a5607b13c00bcb7"
    serializer = NoticeboardRoom(data=request.data)
    if serializer.is_valid():
        db.save("noticeboard_room", org_id, serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_room(request, org_id):
    """Gets all the rooms created under the Noticeboard plugin."""
    if request.method == "GET":
        # org_id = "613a1a3b59842c7444fb0220"
        # org_id = "6145b49e285e4a18402073bc"
        # org_id = "614679ee1a5607b13c00bcb7"
        data = db.read("noticeboard_room", org_id)
        return Response(data)
    return Response(status=status.HTTP_404_NOT_FOUND)




@api_view(["POST"])
def create_notice_view(request, org_id):
    """Create new notices"""
    # org_id = "613a1a3b59842c7444fb0220"

    serializer = CreateNoticeSerializer(data=request.data)
    if serializer.is_valid():
        db.save(
            "noticeboard",
            # "613a1a3b59842c7444fb0220",
            org_id,
            notice_data=serializer.data,
        )

        updated_data = db.read("noticeboard", org_id)

        # created_notice = {
        #     "event":"create_notice",
        #     "data": updated_data
        # }

        user_id = request.GET.get("user")

        update_notice = {
            "event": "sidebar_update",
            "plugin_id": "noticeboard.zuri.chat",
            "data": {
                "name": "Noticeboard Plugin",
                "group_name": "Noticeboard",
                "show_group": False,
                "button_url": "/noticeboard",
                "public_rooms": [],
                "joined_rooms": user_rooms(org_id, user_id),
            },
        }

        # response = requests.get(f"https://noticeboard.zuri.chat/api/v1/organisation/{org_id}/get-room")
        # room = response.json()
        # room_id = room["data"][0]["_id"]

        # db.post_to_centrifugo("team-aquinas-zuri-challenge-007",created_notice)
        db.post_to_centrifugo("team-aquinas-zuri-challenge-007", updated_data)
        db.post_to_centrifugo(f"{org_id}_{user_id}_sidebar", update_notice)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def update_notice_view(request, obj_id, org_id):
    """Update A Notice In A Database."""
    # org_id = "613a1a3b59842c7444fb0220"
    serializer = CreateNoticeSerializer(data=request.data)
    if serializer.is_valid():
        db.update("noticeboard", org_id, serializer.data, object_id=obj_id)

        data = db.read("noticeboard", org_id)

        # updated_data = {
        #     "event":"update_notice",
        #     "data":data
        # }

        # response = requests.get(f"https://noticeboard.zuri.chat/api/v1/organisation/{org_id}/get-room")
        # room = response.json()
        # room_id = room["data"][0]["_id"]

        # db.post_to_centrifugo("team-aquinas-zuri-challenge-007", updated_data)
        db.post_to_centrifugo("team-aquinas-zuri-challenge-007", data)

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": "Notice has been successfully updated",
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"success": False, "message": "Notice not updated, Please Try Again"},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["DELETE"])
def delete_notice(request, object_id, org_id):
    """Delete a notice from the database."""
    # org_id = "613a1a3b59842c7444fb0220"
    if request.method == "DELETE":
        deleted_data = db.delete(
            collection_name="noticeboard", org_id=org_id, object_id=object_id
        )

        data = db.read("noticeboard", org_id)

        # updated_data = {
        #     "event":"delete_notice",
        #     "data":data
        # }

        # response = requests.get(f"https://noticeboard.zuri.chat/api/v1/organisation/{org_id}/get-room")
        # room = response.json()
        # room_id = room["data"][0]["_id"]

        # db.post_to_centrifugo("team-aquinas-zuri-challenge-007", updated_data)
        db.post_to_centrifugo("team-aquinas-zuri-challenge-007", data)

        if deleted_data["status"] == 200:
            return Response(
                {"success": True, "message": "Delete Operation Successful"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Delete Operation Failed. Object does not exist in the database",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def view_notice(request, org_id):
    """This endpoint returns all the notices created under a particular
    organisation in the database."""
    if request.method == "GET":
        # org_id = "613a1a3b59842c7444fb0220"
        notice = db.read("noticeboard", org_id)
        get_data = notice["data"]
        reversed_list = get_data[::-1]
        print(reversed_list)
        notice.update(data=reversed_list)
        if notice["status"] == 200:
            print(notice)
            return Response(notice, status=status.HTTP_200_OK)
        return Response(
            {"status": False, "message": "retrieved unsuccessfully"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


def count_views(data, user):
    """This method is used to count the number views for notices."""
    user_list = list(data.split(" "))
    user_list.append(user)
    user_array = sorted(set(user_list))
    user_string = " ".join([str(elem) for elem in user_array])
    return user_string


@api_view(["GET"])
def notice_detail(request, obj_id, org_id):
    """This returns the detail of a particular notice under the
    organisation."""
    # org_id = "613a1a3b59842c7444fb0220"
    notice = db.read("noticeboard", org_id, filter={"id": obj_id})
    if notice["status"] == 200:
        get_data = notice["data"]
        query = request.GET.get("query")
        if query:
            views = get_data["views"]
            count = count_views(views, query)
            get_data["views"] = count
            serializer = CreateNoticeSerializer(data=get_data)
            if serializer.is_valid():
                db.update("noticeboard", org_id, serializer.data, object_id=id)
                return Response(
                    {
                        "status": True,
                        "data": notice["data"],
                        "message": "sucessfully retrieved",
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "status": True,
                    "data": notice["data"],
                    "message": "sucessfully retrieved",
                },
                status=status.HTTP_200_OK,
            )
    return Response(
        {"status": False, "message": "retrieved unsuccessfully"},
        status=status.HTTP_404_NOT_FOUND,
    )


class NoticeReminder(views.APIView):
    """For creating reminders."""

    newly_created_notice_reminder = []  # stores newly created notice reminder to a list

    @swagger_auto_schema(request_body=NoticeReminderSerializer)
    def post(self, request, org_id):
        """The function accepts a post request for creating reminders."""
        # notice_id=request.GET.get('notice')
        # sendReminderEmail = request.GET.get('sendReminderEmail')

        serializer = NoticeReminderSerializer(data=request.data)
        if serializer.is_valid():
            db.save(
                "reminders",
                org_id,
                # notice_id,
                notice_data=serializer.data,
            )

            # Appends serializer data to newly_created_notice_reminder list
            created_notice_reminder = serializer.data
            self.newly_created_notice_reminder.append(created_notice_reminder)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self):
        """A dummy public method to get past pylint."""
        ...


@api_view(["GET"])
def view_notice_reminder(request, org_id):
    """This endpoint enables user view notices to be reminded of."""
    if request.method == "GET":
        # org_id = "613a1a3b59842c7444fb0220"

        remind_notice = db.read("reminders", org_id)
        print(remind_notice)
        if remind_notice["status"] == 200:
            return Response(remind_notice, status=status.HTTP_200_OK)
        return Response(
            {"status": False, "message": "There are no notices to be reminded of."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def bookmark_notice(request, org_id, user_id):
    """Retrieve all the notices a particular user has bookmarked."""
    if request.method == "GET":
        bookmarked_notices = db.read(
            "bookmark_notice", org_id, filter={"user_id": user_id}
        )
        if bookmarked_notices["status"] == 200:
            return Response(bookmarked_notices, status=status.HTTP_200_OK)
        return Response(
            {"message": "Notice does not exist"}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def create_bookmark(request, org_id):
    """This endpoint enables a user to bookmark a notice."""
    serializer = BookmarkNoticeSerializer(data=request.data)
    if serializer.is_valid():

        # bookmark_data = {
        #     "user_id":serializer.data["user_id"],
        #     "notice_data":notice["data"]
        # }

        bookmarked_data = db.save("bookmark_notice", org_id, serializer.data)

        # response = requests.get(f"https://noticeboard.zuri.chat/api/v1/organisation/{org_id}/get-room")
        # room = response.json()
        # room_id = room["data"][0]["_id"]

        # notice = db.read('noticeboard',org_id, filter={"_id":serializer.data["notice_id"]})

        # data = {
        #     "event":"create_bookmark",
        #     "data":notice["data"]
        # }

        # db.post_to_centrifugo("team-aquinas-zuri-challenge-007", data)
        db.post_to_centrifugo("team-aquinas-zuri-challenge-007", bookmarked_data)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_bookmarked_notice(request, org_id, obj_id):
    """This endpoint enables a user delete a bookmarked notice."""
    if request.method == "DELETE":
        bookmarked_notice = db.delete(org_id, "bookmark_notice", obj_id)

        bookmarked_data = db.read("bookmark_notice", org_id)

        # data = {
        #     "event":"delete_bookmark",
        #     "data":bookmarked_data
        # }

        # response = requests.get(f"https://noticeboard.zuri.chat/api/v1/organisation/{org_id}/get-room")
        # room = response.json()
        # room_id = room["data"][0]["_id"]

        # db.post_to_centrifugo("team-aquinas-zuri-challenge-007", data)
        db.post_to_centrifugo("team-aquinas-zuri-challenge-007", bookmarked_data)

        if bookmarked_notice["status"] == 200:
            return Response(
                {"message": "successfully deleted bookmarked notice"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"message": "could not delete bookmarked notice"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def notice_draft(request, org_id):
    """For creating Drafts for A Notice."""
    serializer = DraftSerializer(data=request.data)
    if serializer.is_valid():
        db.save("noticeboard", org_id, notice_data=serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@swagger_auto_schema(request_body=SchedulesSerializer)
def schedule_notices(request, org_id):
    """For scheduling notices."""

    print(org_id)
    serializer = SchedulesSerializer(data=request.data)
    if serializer.is_valid():
        schDb.scheduleSave("schedules", notice_data=serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def view_schedule(request, org_id):
    """This endpoint returns all the notices created under a particular
    organisation in the database."""
    if request.method == "GET":
        # org_id = "613a1a3b59842c7444fb0220"
        print(org_id)
        notice = schDb.scheduleRead("schedules", " ")
        get_data = notice["data"]
        reversed_list = get_data[::-1]
        print(reversed_list)
        notice.update(data=reversed_list)
        if notice["status"] == 200:
            print(notice)
            return Response(notice, status=status.HTTP_200_OK)
        return Response(
            {"status": False, "message": "retrieved unsuccessfully"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST", "DELETE"])
def attach_file(request, org_id):
    """This endpoint is a send message endpoint that can take files, upload
    them and return the urls to the uploaded files to the media list in the
    message serializer This endpoint uses form data The file must be passed in
    with the key "file"."""

    if request.method == "GET":
        # org_id = "613a1a3b59842c7444fb0220"
        notice = db.read("noticeboard", org_id)
        get_data = notice["data"]
        reversed_list = get_data[::-1]
        print(reversed_list)
        notice.update(data=reversed_list)
        if notice["status"] == 200:
            print(notice)
            return Response(notice, status=status.HTTP_200_OK)
        return Response(
            {"status": False, "message": "retrieved unsuccessfully"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.method == "POST":
        print(request.FILES)
        file_urls = []
        files = request.FILES.getlist("file")

        token = request.META.get("HTTP_AUTHORIZATION")
        if request.FILES and len(files) == 1:
            for file in request.FILES.getlist("file"):
                file_data = db.upload(file=file, token=token)
                if file_data["status"] == 200:
                    for datum in file_data["data"]["files_info"]:
                        file_urls.append(datum["file_url"])
                    return Response(file_data)
                return Response(file_data)
        return Response({"success": False, "message": "No file has been attached"})

    return Response(status=status.HTTP_400_BAD_REQUEST)


# NEW EMAIL NOTIFICATION
@api_view(["GET"])
def email_notification(request):
    """
    This endpoint is used to send email notifications to subscribed users
    when new notices are published.
    """
    if request.method == "GET":
        org_id = request.GET.get("org")
        # user_id = request.GET.get("user")
        send_email = request.GET.get("sendemail")

        if org_id and send_email == "true":
            response_subscribers = db.read("email_subscribers", org_id)

            if response_subscribers["status"] == 200 and response_subscribers["data"]:
                email_subscribers = response_subscribers["data"]

                # email sending setup
                url = "https://api.zuri.chat/external/send-mail?custom_mail=1"

                for user in email_subscribers:
                    email = user["email"]
                    payload = {
                        "email": email,
                        "subject": "notice",
                        "content_type": "text/html",
                        "mail_body": '<div style="background-color: chocolate; width: 100%; height: 50%;"><h1 style="color: white; text-align: center; padding: 1em">Noticeboard Plugin</h2></div><div style="margin: 0% 5% 10% 5%;"><h2>New Notice</h2><p>Hey!</p><br><p>You have a new notice!</p><p>Visit <a href="https://zuri.chat/">zuri chat</a> to view notice.</p><br><p>Cheers,</p><p>Noticeboard Plugin</p></div>',
                    }
                    requests.post(url=url, json=payload)

                return Response(
                    {"status": "emails sent successfully"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": response_subscribers["message"]},
                status=response_subscribers["status"],
            )

        return Response(
            {
                "status": "no emails sent, check if org is not null or if send has a boolean value of true"
            }
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def email_subscription(request):
    """
    This endpoint is used to allow users subscribe to receiving email
    notifications when new notices are published.
    """
    if request.method == "POST":
        org_id = request.GET.get("org")
        user_id = request.GET.get("user")

        if org_id and user_id:  # and user_id
            serializer = SubscribeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_email = serializer.data["email"]
            user_data = {"user_id": user_id, "email": user_email}

            response_subscribers = db.read("email_subscribers", org_id)

            if response_subscribers["status"] == 200 and response_subscribers["data"]:
                for user_obj in response_subscribers["data"]:
                    if user_id == user_obj["user_id"]:
                        return Response(
                            {"status": "already subscribed"},
                            status=status.HTTP_409_CONFLICT,
                        )

                # if user_id doesn't exist, then the user is subscribed
                db.save("email_subscribers", org_id, user_data)
                subscription_success_mail(email=user_email)
                return Response(
                    {"status": "subscription successful", "data": user_data},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {"status": response_subscribers["message"]},
                status=response_subscribers["status"],
            )

        return Response(
            {"status": "no action taken, check org and/or user parameter values"}
        )
    return Response(status=status.HTTP_404_NOT_FOUND)
