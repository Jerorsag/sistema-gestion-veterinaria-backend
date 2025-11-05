"""
Configuración del panel de administración para el módulo de Consultas.

Registra los modelos con interfaces personalizadas para gestión desde /admin/
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Consulta,
    HistoriaClinica,
    Prescripcion,
    Examen,
    HistorialVacuna
)

# Mostrar modelos relacionados dentro de otros

class PrescripcionInline(admin.TabularInline):
    """
    Inline para mostrar prescripciones dentro de una consulta.
    Permite agregar/editar medicamentos directamente desde la consulta.
    """
    model = Prescripcion
    extra = 1  # Número de formularios vacíos a mostrar
    min_num = 0  # Mínimo de prescripciones (puede no tener ninguna)

    fields = ['medicamento', 'cantidad', 'indicaciones']
    autocomplete_fields = ['medicamento']  # Búsqueda autocompletable

    verbose_name = "Prescripción"
    verbose_name_plural = "Prescripciones (Medicamentos)"


class ExamenInline(admin.TabularInline):
    """
    Inline para mostrar exámenes dentro de una consulta.
    """
    model = Examen
    extra = 1
    min_num = 0

    fields = ['tipo_examen', 'descripcion']

    verbose_name = "Examen"
    verbose_name_plural = "Exámenes a Realizar"


class HistorialVacunaInline(admin.StackedInline):
    """
    Inline para mostrar registro de vacunas dentro de una consulta.
    Usa StackedInline porque tiene más campos.
    """
    model = HistorialVacuna
    extra = 0
    max_num = 1  # Solo 1 registro de vacunas por consulta

    fields = ['estado', 'vacunas_descripcion']

    verbose_name = "Estado de Vacunación"
    verbose_name_plural = "Estado de Vacunación"

# ADMIN: CONSULTA (Principal)
@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    """
    Administración de Consultas Veterinarias.
    """

    list_display = [
        'id',
        'mascota_link',
        'veterinario_link',
        'fecha_consulta',
        'diagnostico_corto',
        'total_prescripciones_display',
        'total_examenes_display',
        'estado_vacunacion_display',
        'created_at'
    ]

    # Filtros laterales
    list_filter = [
        'fecha_consulta',
        'veterinario',
        'created_at',
    ]

    # Campos de búsqueda
    search_fields = [
        'mascota__nombre',
        'mascota__propietario__first_name',
        'mascota__propietario__last_name',
        'diagnostico',
        'descripcion_consulta',
    ]

    # Navegación por fecha
    date_hierarchy = 'fecha_consulta'

    # Orden por defecto
    ordering = ['-fecha_consulta']

    # Campos de solo lectura
    readonly_fields = [
        'created_at',
        'updated_at',
        'datos_personales_display',
        'total_prescripciones_display',
        'total_examenes_display',
    ]

    # Autocompletado para relaciones
    autocomplete_fields = ['veterinario', 'mascota']

    # Organización de campos en el formulario
    fieldsets = (
        ('Información General', {
            'fields': (
                'mascota',
                'veterinario',
                'fecha_consulta',
            )
        }),
        ('Datos de la Consulta', {
            'fields': (
                'datos_personales_display',
                'descripcion_consulta',
                'diagnostico',
                'notas_adicionales',
            )
        }),
        ('🕐 Auditoría', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    # Inlines (modelos anidados)
    inlines = [
        HistorialVacunaInline,
        PrescripcionInline,
        ExamenInline,
    ]

    # Paginación
    list_per_page = 25

    @admin.display(description='Mascota', ordering='mascota__nombre')
    def mascota_link(self, obj):
        """Muestra el nombre de la mascota """
        url = reverse('admin:mascotas_mascota_change', args=[obj.mascota.id])
        return format_html('<a href="{}">{}</a>', url, obj.mascota.nombre)

    @admin.display(description='Veterinario', ordering='veterinario__first_name')
    def veterinario_link(self, obj):
        """Muestra el veterinario"""
        if obj.veterinario and hasattr(obj.veterinario, 'user'):
            url = reverse('admin:auth_user_change', args=[obj.veterinario.user.id])
            nombre = obj.veterinario.user.get_full_name() or obj.veterinario.user.username
            return format_html('<a href="{}">{}</a>', url, nombre)
        return '-'

    @admin.display(description='Diagnóstico')
    def diagnostico_corto(self, obj):
        """Muestra versión corta del diagnóstico"""
        if len(obj.diagnostico) > 50:
            return f"{obj.diagnostico[:50]}..."
        return obj.diagnostico

    @admin.display(description='Datos Personales')
    def datos_personales_display(self, obj):
        """Muestra los datos personales de la mascota en formato HTML"""
        datos = obj.get_datos_personales()
        return format_html(
            f"Mascota: {datos['nombre_mascota']}\n"
            f"Propietario: {datos['nombre_propietario']}\n"
            f"Edad: {datos['edad']}\n"
            f"Especie: {datos['tipo_especie']}\n"
            f"Raza: {datos['raza']}\n"
            f"Estado Vacunación: {datos['estado_vacunacion']}"
        )

    @admin.display(description='Prescripciones')
    def total_prescripciones_display(self, obj):
        """Muestra el total de prescripciones"""
        total = obj.get_prescripciones_count()
        if total > 0:
            return f"{total} medicamentos"
        return "Sin prescripciones"

    @admin.display(description='Exámenes')
    def total_examenes_display(self, obj):
        """Muestra el total de exámenes"""
        total = obj.get_examenes_count()
        if total > 0:
            return f"{total} medicamentos"
        return "Sin examenes"

    @admin.display(description='Vacunación')
    def estado_vacunacion_display(self, obj):
        """Muestra el estado de vacunación con color"""
        estado = obj.get_estado_vacunacion_consulta()
        return estado or "No registrado"

    actions = ['exportar_consultas']

# ADMIN: HISTORIA CLÍNICA

@admin.register(HistoriaClinica)
class HistoriaClinicaAdmin(admin.ModelAdmin):
    """
    Administración de Historias Clínicas consolidadas.
    """

    list_display = [
        'id',
        'mascota_link',
        'propietario_display',
        'total_consultas_display',
        'estado_vacunacion_badge',
        'fecha_actualizacion'
    ]

    list_filter = [
        'estado_vacunacion_actual',
        'fecha_creacion',
        'fecha_actualizacion',
    ]

    search_fields = [
        'mascota__nombre',
        'mascota__cliente__usuario__nombre',
        'mascota__cliente__usuario__apellido',
    ]

    date_hierarchy = 'fecha_actualizacion'

    ordering = ['-fecha_actualizacion']

    readonly_fields = [
        'mascota',
        'fecha_creacion',
        'fecha_actualizacion',
        'estado_vacunacion_actual',
        'total_consultas_display',
        'ultima_consulta_display',
        'medicamentos_frecuentes_display',
    ]

    fieldsets = (
        ('Mascota', {
            'fields': (
                'mascota',
                'total_consultas_display',
            )
        }),
        ('Vacunación', {
            'fields': (
                'estado_vacunacion_actual',
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',),
        }),
    )

    # Deshabilitar agregar/eliminar (se crea automáticamente)
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Mascota', ordering='mascota__nombre')
    def mascota_link(self, obj):
        """Link a la mascota"""
        url = reverse('admin:mascotas_mascota_change', args=[obj.mascota.id])
        return format_html('<a href="{}">{}</a>', url, obj.mascota.nombre)

    @admin.display(description='Propietario')
    def propietario_display(self, obj):
        return obj.mascota.cliente.get_full_name() if hasattr(obj.mascota.cliente, 'get_full_name') else str(
            obj.mascota.cliente)

    @admin.display(description='Total Consultas')
    def total_consultas_display(self, obj):
        """Muestra el total de consultas como un enlace al listado filtrado."""
        total = obj.get_total_consultas()

        # URL del admin de consultas filtrada por mascota
        url = reverse('admin:consultas_consulta_changelist') + f'?mascota__id__exact={obj.mascota.id}'

        return format_html(
            '<a href="{}" style="background-color: #ffff; padding: 5px 10px; border-radius: 3px; '
            'text-decoration: none; color: #000;">'
            '<strong>{}</strong> consulta(s)</a>',
            url,
            total
        )

    @admin.display(description='Estado Vacunación')
    def estado_vacunacion_badge(self, obj):
        """Badge con color según estado"""
        estado = obj.get_estado_vacunacion_actual_display()

        return f"{estado}"

    @admin.display(description='Última Consulta')
    def ultima_consulta_display(self, obj):
        """Muestra info de la última consulta"""
        ultima = obj.get_ultima_consulta()
        if ultima:
            return format_html(
                '<strong>Fecha:</strong> {}<br>'
                '<strong>Diagnóstico:</strong> {}',
                ultima.fecha_consulta.strftime('%d/%m/%Y'),
                ultima.diagnostico[:50]
            )
        return 'Sin consultas'

    @admin.display(description='Medicamentos Frecuentes')
    def medicamentos_frecuentes_display(self, obj):
        """Lista de medicamentos más prescritos en texto plano"""
        medicamentos = obj.get_medicamentos_frecuentes(limit=3)
        if medicamentos:
            # Creamos una lista de strings "Nombre (cantidadx)"
            lista_meds = [f"{med['medicamento__nombre']} ({med['cantidad_prescripciones']}x)" for med in medicamentos]
            # Unimos todo con comas
            return ", ".join(lista_meds)
        return 'Sin prescripciones'

# ADMIN: PRESCRIPCIÓN

@admin.register(Prescripcion)
class PrescripcionAdmin(admin.ModelAdmin):
    """
    Administración de Prescripciones.
    """
    list_display = [
        'id',
        'consulta_link',
        'mascota_display',
        'medicamento_link',
        'cantidad',
        'stock_disponible_display',
        'fecha_prescripcion'
    ]

    list_filter = [
        'fecha_prescripcion',
        'medicamento',
    ]

    search_fields = [
        'consulta__mascota__nombre',
        'medicamento__descripcion',
        'indicaciones',
    ]

    date_hierarchy = 'fecha_prescripcion'

    ordering = ['-fecha_prescripcion']

    readonly_fields = ['fecha_prescripcion', 'stock_disponible_display']

    autocomplete_fields = ['consulta', 'medicamento']

    fieldsets = (
        ('Consulta', {
            'fields': ('consulta',)
        }),
        ('Medicamento', {
            'fields': (
                'medicamento',
                'cantidad',
                'stock_disponible_display',
                'indicaciones',
            )
        }),
        ('Fecha', {
            'fields': ('fecha_prescripcion',),
            'classes': ('collapse',),
        }),
    )


    @admin.display(description='Consulta')
    def consulta_link(self, obj):
        """Link a la consulta"""
        url = reverse('admin:consultas_consulta_change', args=[obj.consulta.id])
        return format_html(
            '<a href="{}">Consulta #{}</a>',
            url,
            obj.consulta.id
        )

    @admin.display(description='Mascota')
    def mascota_display(self, obj):
        """Muestra la mascota"""
        return obj.consulta.mascota.nombre

    @admin.display(description='Medicamento')
    def medicamento_link(self, obj):
        """Link al medicamento"""
        url = reverse('admin:inventario_producto_change', args=[obj.medicamento.id])
        return format_html('<a href="{}">{}</a>', url, obj.medicamento.descripcion)

    @admin.display(description='Stock Disponible')
    def stock_disponible_display(self, obj):
        """Muestra stock con color"""
        stock = obj.medicamento.stock

        if stock <= obj.medicamento.stock_minimo:
            color = 'red'
        elif stock <= obj.medicamento.stock_minimo * 2:
            color = 'orange'
        else:
            color = 'green'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {} unidades</span>',
            color,
            stock,
            obj.medicamento.descripcion
        )

# ADMIN: EXAMEN

@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    """
    Administración de Exámenes.
    """

    list_display = [
        'id',
        'consulta_link',
        'mascota_display',
        'tipo_examen_badge',
        'descripcion_corta',
        'fecha_orden'
    ]

    list_filter = [
        'tipo_examen',
        'fecha_orden',
    ]

    search_fields = [
        'consulta__mascota__nombre',
        'descripcion',
        'tipo_examen',
    ]

    date_hierarchy = 'fecha_orden'

    ordering = ['-fecha_orden']

    readonly_fields = ['fecha_orden']

    autocomplete_fields = ['consulta']

    fieldsets = (
        ('Consulta', {
            'fields': ('consulta',)
        }),
        ('Examen', {
            'fields': (
                'tipo_examen',
                'descripcion',
            )
        }),
        ('Fecha', {
            'fields': ('fecha_orden',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Consulta')
    def consulta_link(self, obj):
        """Link a la consulta"""
        url = reverse('admin:consultas_consulta_change', args=[obj.consulta.id])
        return format_html('<a href="{}">Consulta #{}</a>', url, obj.consulta.id)

    @admin.display(description='Mascota')
    def mascota_display(self, obj):
        """Muestra la mascota"""
        return obj.consulta.mascota.nombre

    @admin.display(description='Tipo de Examen')
    def tipo_examen_badge(self, obj):
        """Badge del tipo de examen"""
        return obj.get_tipo_examen_display()

    @admin.display(description='Descripción')
    def descripcion_corta(self, obj):
        """Versión corta de la descripción"""
        if obj.descripcion:
            if len(obj.descripcion) > 50:
                return f"{obj.descripcion[:50]}..."
            return obj.descripcion
        return '-'

# ADMIN: HISTORIAL DE VACUNAS

@admin.register(HistorialVacuna)
class HistorialVacunaAdmin(admin.ModelAdmin):
    """
    Administración de Historial de Vacunas.
    """

    list_display = [
        'id',
        'consulta_link',
        'mascota_display',
        'estado_badge',
        'vacunas_descripcion_corta',
        'fecha_registro'
    ]

    list_filter = [
        'estado',
        'fecha_registro',
    ]

    search_fields = [
        'consulta__mascota__nombre',
        'vacunas_descripcion',
    ]

    date_hierarchy = 'fecha_registro'

    ordering = ['-fecha_registro']

    readonly_fields = ['fecha_registro']

    autocomplete_fields = ['consulta']

    fieldsets = (
        ('Consulta', {
            'fields': ('consulta',)
        }),
        ('Vacunación', {
            'fields': (
                'estado',
                'vacunas_descripcion',
            )
        }),
        ('Fecha', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Consulta')
    def consulta_link(self, obj):
        """Link a la consulta"""
        url = reverse('admin:consultas_consulta_change', args=[obj.consulta.id])
        return format_html('<a href="{}">Consulta #{}</a>', url, obj.consulta.id)

    @admin.display(description='Mascota')
    def mascota_display(self, obj):
        """Muestra la mascota"""
        return obj.consulta.mascota.nombre

    @admin.display(description='Estado')
    def estado_badge(self, obj):
        """Badge con color según estado"""
        estado = obj.get_estado_display()


        return estado

    @admin.display(description='Vacunas')
    def vacunas_descripcion_corta(self, obj):
        """Versión corta de vacunas"""
        if obj.vacunas_descripcion:
            if len(obj.vacunas_descripcion) > 40:
                return f"{obj.vacunas_descripcion[:40]}..."
            return obj.vacunas_descripcion
        return format_html('<span style="color: gray;">-</span>')