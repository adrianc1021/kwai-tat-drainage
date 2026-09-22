from django.db import migrations


NEW_ORIGIN = 'https://rapidflowhk.com'
OLD_ORIGINS = (
    'https://kwai-tat-drainage-cms.onrender.com',
    'https://kwai-tat-drainage.onrender.com',
    'http://kwai-tat-drainage-cms.onrender.com',
    'http://kwai-tat-drainage.onrender.com',
)


def replace_origins(value):
    if isinstance(value, str):
        for old in OLD_ORIGINS:
            value = value.replace(old, NEW_ORIGIN)
        return value
    if isinstance(value, list):
        return [replace_origins(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_origins(item) for key, item in value.items()}
    return value


def migrate_domain(apps, schema_editor):
    SeoMetadata = apps.get_model('cms', 'SeoMetadata')
    Redirect = apps.get_model('cms', 'Redirect')
    Page = apps.get_model('cms', 'Page')

    for row in SeoMetadata.objects.exclude(canonical=''):
        canonical = replace_origins(row.canonical)
        if canonical != row.canonical:
            row.canonical = canonical
            row.save(update_fields=['canonical', 'updated_at'])

    for row in Redirect.objects.all():
        target = replace_origins(row.target)
        if target != row.target:
            row.target = target
            row.save(update_fields=['target'])

    for row in Page.objects.all():
        draft = replace_origins(row.draft)
        published = replace_origins(row.published)
        if draft != row.draft or published != row.published:
            row.draft = draft
            row.published = published
            row.save(update_fields=['draft', 'published', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('cms', '0005_sitesettings_brand_copy')]

    operations = [migrations.RunPython(migrate_domain, migrations.RunPython.noop)]
