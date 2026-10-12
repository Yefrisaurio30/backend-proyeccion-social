from django.conf import settings


def get_supabase_client():
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def upload_image(file, filename):
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET

    file_bytes = file.read()
    content_type = file.content_type or 'image/jpeg'

    client.storage.from_(bucket).upload(
        path=filename,
        file=file_bytes,
        file_options={"content-type": content_type},
    )

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"
    return public_url


def delete_image(filename):
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET
    client.storage.from_(bucket).remove([filename])
