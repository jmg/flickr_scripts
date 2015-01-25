import flickrapi
import webbrowser
import os

API_KEY = u"995f1b5f7110a1828ab4898be30d3335"
API_SECRET = u"903b47efa77d34f8"

flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format='parsed-json')


def auth():
    """
        Authenticate the app with flickr.
        Requests for all permissions (read, write and delete)
    """
    permissions = u'delete'
    if not flickr.token_valid(perms=permissions):

        flickr.get_request_token(oauth_callback=u'oob')

        authorize_url = flickr.auth_url(perms=permissions)
        webbrowser.open_new_tab(authorize_url)

        verifier = unicode(raw_input('Verifier code: '))
        flickr.get_access_token(verifier)


def remove_duplicated_photos():
    """
        Remove all duplicated photos by name
    """
    photos = []
    duplicated = 0
    for photo in get_photostream():
        if not photo["title"] in photos:
            photos.append(photo["title"])
        else:
            print "Deleting duplicated photo: %s" % photo["title"]
            duplicated += 1
            flickr.photos.delete(photo_id=photo["id"])
    print "Removed %s duplicated photos" % duplicated


def get_photostream():
    stream = flickr.people.getPhotos(user_id="me")
    return stream["photos"]["photo"]


def get_albums():
    response = flickr.photosets.getList()
    return response["photosets"]["photoset"]


def find_album(album_name):
    for photoset in get_albums():
        if album_name.lower().strip() == photoset["title"]["_content"].lower().strip():
            return photoset


def add_photo_stream_to_album(album_name):
    """
        Move photos on the photostream to a given album
    """
    photoset = find_album(album_name)

    if photoset is None:
        print "Album not found"
        return

    for photo in get_photostream():
        print "Adding %s to %s" % (photo["title"], photoset["title"]["_content"])
        flickr.photosets.addPhoto(photoset_id=photoset["id"], photo_id=photo["id"])


def upload_photos_in_dir(directory, album_name=None):
    """
        Uploads all photos in a directory to flickr.
        The album_name is optional.
    """
    photos_names = [photo["title"] for photo in get_photostream()]

    photoset = None
    if album_name is not None:
        photoset = find_album(album_name)
        if photoset is None:
            print "Album not found"
            return

    tries = 3
    uploads = 1
    files = os.listdir(directory)
    for file_name in files:
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):

            if file_name in photos_names:
                print "%s already uploaded" % file_name
                uploads += 1
                continue

            with open(file_path) as file_obj:

                photo_data = {
                    "filename": file_name,
                    "title": file_name,
                    "fileobj": file_obj,
                    "is_public": False,
                    "is_family": True,
                    "is_friend": True,
                    "format": "etree",
                }

                print "Uploading %s/%s: %s" % (uploads, len(files), file_name)

                response = None
                for x in range(tries):
                    try:
                        response = flickr.upload(**photo_data)
                        break
                    except:
                        print "Error uploading: %s. Retrying..." % file_name

                if response is None:
                    print "Could not upload: %s" % file_name
                    continue

                photo_id = response[0].text
                if photoset is not None:
                    flickr.photosets.addPhoto(photoset_id=photoset["id"], photo_id=photo_id)

                uploads += 1


if __name__ == "__main__":

    auth()
    #get_albums()
    #remove_duplicated_photos()
    #add_photo_stream_to_album("Mar Del Plata 2015")
    upload_photos_in_dir("/home/jm/Pictures/Mar del plata 2015/Seleccion/", album_name="Mar Del Plata 2015")