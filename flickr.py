import flickrapi
import webbrowser
import os
import threading

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
    stream = flickr.people.getPhotos(user_id="me", per_page=500)
    photos = stream["photos"]["photo"]
    if stream["photos"]["pages"] > 1:
        for page in range(1, stream["photos"]["pages"]+1):
            more_photos = flickr.people.getPhotos(user_id="me", per_page=500, page=page+1)
            photos.extend(more_photos["photos"]["photo"])
    return photos


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


def upload_photos(files, directory, photoset):

    MAX_TRIES = 3
    uploads = 1
    current_thread_name = threading.current_thread().getName()

    for (file_name, file_path) in files:

        for x in range(MAX_TRIES):
            try:
                file_obj = open(file_path)
                photo_data = {
                    "filename": file_name,
                    "title": file_name,
                    "fileobj": file_obj,
                    "is_public": False,
                    "is_family": True,
                    "is_friend": True,
                    "format": "etree",
                }

                print "%s: Uploading %s/%s: %s" % (current_thread_name, uploads, len(files), file_name)

                response = None
                response = flickr.upload(**photo_data)
                break
            except Exception, e:
                print "%s: Error uploading: %s. Retrying...\n%s" % (current_thread_name, file_name, e)
            finally:
                file_obj.close()

        if response is None:
            print "Could not upload: %s" % file_name
            continue

        photo_id = response[0].text
        if photoset is not None:
            flickr.photosets.addPhoto(photoset_id=photoset["id"], photo_id=photo_id)

        uploads += 1


def chunks(l, n):
    """
        Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def is_valid_extension(extension):

    for valid_extension in ["jpg", "png"]:
        if valid_extension == extension.lower():
            return True
    return False


def upload_photos_in_dir(directory, album_name=None):
    """
        Uploads all photos in a directory to flickr.
        The album_name is optional.
    """
    files = os.listdir(directory)
    upload_files = []
    already_uploaded = []
    photostream = get_photostream()
    photos_names = [photo["title"] for photo in photostream]

    for file_name in files:
        if file_name in photos_names:
            already_uploaded.append(file_name)
        else:
            file_path = os.path.join(directory, file_name)
            _, file_extension = os.path.splitext(file_path)

            if os.path.isfile(file_path) and is_valid_extension(file_extension[1:]):
                upload_files.append((file_name, file_path))

    THREADING = 2
    print "*" * 40
    print "Already uploaded: %s" % len(already_uploaded)
    print "To upload: %s" % len(upload_files)
    print "Number of workers: %s" % THREADING
    print "*" * 40

    if not upload_files:
        print "No files to upload"

    photoset = None
    if album_name is not None:
        photoset = find_album(album_name)
        if photoset is None:
            print "Album not found"
            return

    files_chunks = list(chunks(upload_files, len(upload_files) / THREADING))

    pool = []

    for i in range(THREADING):

        thread = threading.Thread(target=upload_photos, args=(files_chunks[i], directory, photoset))
        thread.start()
        pool.append(thread)

    for thread in pool:
        thread.join()


if __name__ == "__main__":

    auth()
    #photos = get_photostream()
    #import ipdb; ipdb.set_trace()

    #remove_duplicated_photos()
    add_photo_stream_to_album("Mar Del Plata 2015")
    #upload_photos_in_dir("/home/jm/Pictures/Mar del plata 2015/Seleccion/", album_name="Mar Del Plata 2015")