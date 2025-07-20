from django.db import migrations

def add_gemini_models(apps, schema_editor):
    AIModel = apps.get_model('posts', 'AIModel')
    AIModel.objects.create(name='gemini-1.5-flash', is_active=True)
    AIModel.objects.create(name='gemini-pro', is_active=False)

class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_aimodel'),
    ]

    operations = [
        migrations.RunPython(add_gemini_models),
    ]
