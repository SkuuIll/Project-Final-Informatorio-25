"""
Vistas para gestión de prompts de IA.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
import json

from .models import AIPromptTemplate
from .forms import AIPromptTemplateForm, PromptPreviewForm
from .prompt_manager import PromptManager, initialize_default_prompts


def is_staff_or_superuser(user):
    """Verificar si el usuario es staff o superuser."""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_or_superuser)
def prompt_list_view(request):
    """Vista para listar todos los prompts."""
    
    # Inicializar prompts por defecto si no existen
    initialize_default_prompts(request.user)
    
    # Filtros
    prompt_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    
    # Query base
    prompts = AIPromptTemplate.objects.all().order_by('-is_default', 'prompt_type', 'name')
    
    # Aplicar filtros
    if prompt_type:
        prompts = prompts.filter(prompt_type=prompt_type)
    
    if search:
        prompts = prompts.filter(name__icontains=search)
    
    # Paginación
    paginator = Paginator(prompts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'prompt_types': AIPromptTemplate.PROMPT_TYPES,
        'current_type': prompt_type,
        'search': search,
    }
    
    return render(request, 'admin/posts/prompt_list.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def prompt_create_view(request):
    """Vista para crear un nuevo prompt."""
    
    if request.method == 'POST':
        form = AIPromptTemplateForm(request.POST)
        if form.is_valid():
            prompt = form.save(commit=False)
            prompt.created_by = request.user
            prompt.save()
            
            messages.success(request, f'Prompt "{prompt.name}" creado exitosamente.')
            return redirect('posts:prompt_list')
    else:
        form = AIPromptTemplateForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Prompt',
        'action': 'Crear'
    }
    
    return render(request, 'admin/posts/prompt_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def prompt_edit_view(request, prompt_id):
    """Vista para editar un prompt existente."""
    
    prompt = get_object_or_404(AIPromptTemplate, id=prompt_id)
    
    if request.method == 'POST':
        form = AIPromptTemplateForm(request.POST, instance=prompt)
        if form.is_valid():
            form.save()
            messages.success(request, f'Prompt "{prompt.name}" actualizado exitosamente.')
            return redirect('posts:prompt_list')
    else:
        form = AIPromptTemplateForm(instance=prompt)
    
    context = {
        'form': form,
        'prompt': prompt,
        'title': f'Editar Prompt: {prompt.name}',
        'action': 'Actualizar'
    }
    
    return render(request, 'admin/posts/prompt_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def prompt_delete_view(request, prompt_id):
    """Vista para eliminar un prompt."""
    
    prompt = get_object_or_404(AIPromptTemplate, id=prompt_id)
    
    if request.method == 'POST':
        if PromptManager.delete_prompt(prompt_id):
            messages.success(request, f'Prompt "{prompt.name}" eliminado exitosamente.')
        else:
            messages.error(request, 'No se puede eliminar el último prompt por defecto.')
        
        return redirect('posts:prompt_list')
    
    context = {
        'prompt': prompt,
        'title': f'Eliminar Prompt: {prompt.name}'
    }
    
    return render(request, 'admin/posts/prompt_delete.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])
def prompt_set_default_view(request, prompt_id):
    """Vista para establecer un prompt como por defecto."""
    
    try:
        prompt = PromptManager.set_default_prompt(prompt_id)
        messages.success(request, f'Prompt "{prompt.name}" establecido como por defecto.')
    except AIPromptTemplate.DoesNotExist:
        messages.error(request, 'Prompt no encontrado.')
    
    return redirect('posts:prompt_list')


@login_required
@user_passes_test(is_staff_or_superuser)
def prompt_preview_view(request):
    """Vista para previsualizar prompts con datos de prueba."""
    
    if request.method == 'POST':
        form = PromptPreviewForm(request.POST)
        if form.is_valid():
            template = form.cleaned_data['template']
            test_content = form.cleaned_data['test_content']
            test_title = form.cleaned_data['test_title']
            test_keywords = form.cleaned_data['test_keywords']
            
            # Generar preview del prompt
            try:
                preview = template.format(
                    content=test_content,
                    title=test_title,
                    keywords=test_keywords,
                    urls="https://example.com/url1, https://example.com/url2",
                    style="professional",
                    size="1024x1024"
                )
                
                context = {
                    'form': form,
                    'preview': preview,
                    'success': True
                }
            except KeyError as e:
                context = {
                    'form': form,
                    'error': f'Variable no encontrada en el template: {e}',
                    'success': False
                }
            except Exception as e:
                context = {
                    'form': form,
                    'error': f'Error al procesar el template: {e}',
                    'success': False
                }
        else:
            context = {'form': form, 'success': False}
    else:
        form = PromptPreviewForm()
        context = {'form': form, 'success': False}
    
    return render(request, 'admin/posts/prompt_preview.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def prompt_ajax_get(request, prompt_id):
    """Vista AJAX para obtener el contenido de un prompt."""
    
    try:
        prompt = AIPromptTemplate.objects.get(id=prompt_id)
        return JsonResponse({
            'success': True,
            'template': prompt.template,
            'name': prompt.name,
            'description': prompt.description
        })
    except AIPromptTemplate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Prompt no encontrado'
        })


@login_required
@user_passes_test(is_staff_or_superuser)
def prompt_duplicate_view(request, prompt_id):
    """Vista para duplicar un prompt existente."""
    
    original_prompt = get_object_or_404(AIPromptTemplate, id=prompt_id)
    
    if request.method == 'POST':
        form = AIPromptTemplateForm(request.POST)
        if form.is_valid():
            new_prompt = form.save(commit=False)
            new_prompt.created_by = request.user
            new_prompt.is_default = False  # Los duplicados nunca son por defecto
            new_prompt.save()
            
            messages.success(request, f'Prompt duplicado como "{new_prompt.name}".')
            return redirect('posts:prompt_list')
    else:
        # Pre-llenar el formulario con los datos del prompt original
        initial_data = {
            'name': f"{original_prompt.name} (Copia)",
            'prompt_type': original_prompt.prompt_type,
            'template': original_prompt.template,
            'description': f"Copia de: {original_prompt.description}",
            'is_default': False
        }
        form = AIPromptTemplateForm(initial=initial_data)
    
    context = {
        'form': form,
        'original_prompt': original_prompt,
        'title': f'Duplicar Prompt: {original_prompt.name}',
        'action': 'Duplicar'
    }
    
    return render(request, 'admin/posts/prompt_form.html', context)