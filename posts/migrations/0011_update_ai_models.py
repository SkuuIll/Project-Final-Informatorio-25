from django.db import migrations

def update_ai_models(apps, schema_editor):
    AIModel = apps.get_model('posts', 'AIModel')
    
    # Desactivar todos los modelos existentes
    AIModel.objects.all().update(is_active=False)
    
    # Crear o actualizar el nuevo modelo de texto
    text_model, created = AIModel.objects.get_or_create(
        name='learnlm-2.0-flash-experimental',
        defaults={'is_active': True}
    )
    if not created:
        text_model.is_active = True
        text_model.save()
    
    # Crear modelo de imagen (aunque se use principalmente para referencia)
    AIModel.objects.get_or_create(
        name='gemini-2.0-flash-preview-image-generation',
        defaults={'is_active': False}
    )

def reverse_update_ai_models(apps, schema_editor):
    AIModel = apps.get_model('posts', 'AIModel')
    
    # Revertir a los modelos anteriores
    AIModel.objects.all().update(is_active=False)
    
    # Reactivar el modelo anterior
    try:
        old_model = AIModel.objects.get(name='gemini-1.5-flash')
        old_model.is_active = True
        old_model.save()
    except AIModel.DoesNotExist:
        # Si no existe, crear el modelo anterior
        AIModel.objects.create(name='gemini-1.5-flash', is_active=True)

class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_aiprompttemplate'),
    ]

    operations = [
        migrations.RunPython(update_ai_models, reverse_update_ai_models),
    ]