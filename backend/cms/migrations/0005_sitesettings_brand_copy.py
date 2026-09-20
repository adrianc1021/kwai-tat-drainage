from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cms', '0004_alter_sitesettings_telephone_and_more')]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='announcement',
            field=models.CharField(default='24 小時接受緊急渠務查詢，實際到場時間由客服確認', max_length=180, verbose_name='公告列文字'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='footer_note',
            field=models.CharField(default='香港通渠及渠務服務，先了解問題，再安排處理。', max_length=240, verbose_name='頁尾簡介'),
        ),
    ]
