#!/usr/bin/env python
"""Script para generar proyectos de prueba"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from models import (
    LearningExperience,
    ISTEStandard,
    Comment,
    User,
)

app = create_app()

TEST_PROJECTS = [
    {
        'title': 'Introducción a Python: Variables y Tipos de Datos',
        'level': '9no-10mo',
        'teacher_profile': 'Docente de Informática',
        'course_focus': 'Programación',
        'learning_objective': 'Los estudiantes comprenderán los conceptos fundamentales de variables y tipos de datos en Python.',
        'classroom_application': 'Se utilizará Python 3 en un entorno interactivo para que los estudiantes creen programas simples.',
        'minimal_technology': 'Computadora con Python 3 instalado',
        'estimated_duration': '90 minutos',
        'workflow_status': 'published',
        'board_stage': 'en_clase',
        'week_slot': 1,
        'planning_markdown': '# Introducción a Python\n\n## Objetivos\n- Comprender variables\n- Conocer tipos de datos\n- Escribir programas básicos\n\n## Actividades\n1. Explicación teórica\n2. Práctica guiada\n3. Proyecto independiente',
        'iste_standards': ['1a', '4a'],
    },
    {
        'title': 'Ciudadanía Digital: Ciberseguridad Básica',
        'level': '7mo-8vo',
        'teacher_profile': 'Docente de Tecnología',
        'course_focus': 'Ciudadanía Digital',
        'learning_objective': 'Los estudiantes aprenderán a protegerse en línea y entenderán los riesgos digitales.',
        'classroom_application': 'Análisis de casos reales y simulaciones de ataques comunes.',
        'minimal_technology': 'Navegador web moderno',
        'estimated_duration': '60 minutos',
        'workflow_status': 'published',
        'board_stage': 'lista',
        'week_slot': 2,
        'planning_markdown': '# Ciudadanía Digital\n\n## Temas\n- Contraseñas seguras\n- Phishing\n- Privacidad en línea',
        'iste_standards': ['3a'],
    },
    {
        'title': 'Robótica: Construye tu Primer Robot',
        'level': '6to-8vo',
        'teacher_profile': 'Docente Especialista en Robótica',
        'course_focus': 'Robótica',
        'learning_objective': 'Los estudiantes diseñarán y construirán un robot básico.',
        'classroom_application': 'Trabajo en equipos pequeños con kits de robótica.',
        'minimal_technology': 'Kit de robótica (LEGO Mindstorms o Arduino)',
        'estimated_duration': '120 minutos',
        'workflow_status': 'published',
        'board_stage': 'en_clase',
        'week_slot': 3,
        'planning_markdown': '# Robótica Básica\n\n## Proyecto\n- Construcción del robot\n- Programación del movimiento\n- Pruebas y ajustes',
        'iste_standards': ['4a', '5a'],
    },
    {
        'title': 'HTML y CSS: Crea tu Página Web',
        'level': '9no-10mo',
        'teacher_profile': 'Docente de Desarrollo Web',
        'course_focus': 'Programación Web',
        'learning_objective': 'Los estudiantes crearán una página web interactiva usando HTML y CSS.',
        'classroom_application': 'Editor de texto y navegador web para visualizar cambios en tiempo real.',
        'minimal_technology': 'Editor de texto (VS Code, Sublime Text)',
        'estimated_duration': '180 minutos',
        'workflow_status': 'draft',
        'board_stage': 'por_planear',
        'week_slot': 1,
        'planning_markdown': '# Desarrollo Web\n\n## Objetivos\n- Estructura HTML\n- Estilos CSS\n- Diseño responsivo',
        'iste_standards': ['4a', '6a'],
    },
    {
        'title': 'Excel Avanzado: Análisis de Datos',
        'level': '8vo-9no',
        'teacher_profile': 'Docente de Ofimática',
        'course_focus': 'Productividad',
        'learning_objective': 'Los estudiantes aprenderán a analizar datos complejos con Excel.',
        'classroom_application': 'Uso de funciones avanzadas y tablas dinámicas.',
        'minimal_technology': 'Microsoft Excel o LibreOffice Calc',
        'estimated_duration': '90 minutos',
        'workflow_status': 'published',
        'board_stage': 'archivada',
        'week_slot': 2,
        'planning_markdown': '# Análisis de Datos con Excel\n\n## Funciones\n- VLOOKUP\n- Pivot Tables\n- Gráficos avanzados',
        'iste_standards': ['2a'],
    },
    {
        'title': 'Inteligencia Artificial: Chatbots con IA',
        'level': '10mo',
        'teacher_profile': 'Docente Especialista en IA',
        'course_focus': 'Inteligencia Artificial',
        'learning_objective': 'Los estudiantes crearán un chatbot simple usando APIs de IA.',
        'classroom_application': 'Uso de plataformas como Dialogflow o Python con librerías de IA.',
        'minimal_technology': 'Acceso a internet y entorno de desarrollo',
        'estimated_duration': '150 minutos',
        'workflow_status': 'published',
        'board_stage': 'lista',
        'week_slot': 4,
        'planning_markdown': '# IA y Chatbots\n\n## Proyecto\n- Configuración de Dialogflow\n- Entrenamiento del modelo\n- Integración en aplicación',
        'iste_standards': ['4a', '5a'],
    },
    {
        'title': 'Fotografía Digital: Edición Básica',
        'level': '7mo-9no',
        'teacher_profile': 'Docente de Artes',
        'course_focus': 'Creatividad Digital',
        'learning_objective': 'Los estudiantes aprenderán técnicas de fotografía digital y edición.',
        'classroom_application': 'Uso de cámaras digitales y software de edición.',
        'minimal_technology': 'Cámara digital o smartphone, software de edición (GIMP/Photoshop)',
        'estimated_duration': '120 minutos',
        'workflow_status': 'draft',
        'board_stage': 'por_planear',
        'week_slot': 1,
        'planning_markdown': '# Fotografía Digital\n\n## Temas\n- Composición\n- Iluminación\n- Edición básica',
        'iste_standards': ['6a'],
    },
    {
        'title': 'Scratch: Crea Historias Interactivas',
        'level': '4to-6to',
        'teacher_profile': 'Docente de Primaria',
        'course_focus': 'Programación Visual',
        'learning_objective': 'Los estudiantes crearán historias interactivas usando bloques visuales.',
        'classroom_application': 'Plataforma Scratch en línea con proyectos colaborativos.',
        'minimal_technology': 'Navegador web con acceso a Scratch',
        'estimated_duration': '60 minutos',
        'workflow_status': 'published',
        'board_stage': 'en_clase',
        'week_slot': 2,
        'planning_markdown': '# Programación con Scratch\n\n## Proyecto\n- Crear personajes\n- Añadir interactividad\n- Compartir el proyecto',
        'iste_standards': ['1a', '4a'],
    },
    {
        'title': 'Base de Datos SQL: Queries Complejas',
        'level': '10mo',
        'teacher_profile': 'Docente de Bases de Datos',
        'course_focus': 'Bases de Datos',
        'learning_objective': 'Los estudiantes escribirán consultas SQL avanzadas.',
        'classroom_application': 'Entorno MySQL o PostgreSQL para prácticas.',
        'minimal_technology': 'Cliente SQL (MySQL Workbench, pgAdmin)',
        'estimated_duration': '90 minutos',
        'workflow_status': 'published',
        'board_stage': 'lista',
        'week_slot': 3,
        'planning_markdown': '# SQL Avanzado\n\n## Consultas\n- JOINs complejos\n- Subconsultas\n- Procedimientos almacenados',
        'iste_standards': ['2a', '4a'],
    },
    {
        'title': 'Git y Control de Versiones',
        'level': '9no-10mo',
        'teacher_profile': 'Docente de Desarrollo',
        'course_focus': 'DevOps',
        'learning_objective': 'Los estudiantes aprenderán a trabajar en equipo con Git.',
        'classroom_application': 'Repositorios en GitHub y flujo de trabajo colaborativo.',
        'minimal_technology': 'Git instalado y cuenta de GitHub',
        'estimated_duration': '120 minutos',
        'workflow_status': 'draft',
        'board_stage': 'por_planear',
        'week_slot': 2,
        'planning_markdown': '# Control de Versiones\n\n## Conceptos\n- Commits\n- Branches\n- Pull Requests\n- Merge',
        'iste_standards': ['5a', '6a'],
    },
    {
        'title': 'Diseño Thinking: Resolviendo Problemas Reales',
        'level': '6to-10mo',
        'teacher_profile': 'Docente Innovador',
        'course_focus': 'Pensamiento Crítico',
        'learning_objective': 'Los estudiantes aplicarán Design Thinking para resolver problemas escolares.',
        'classroom_application': 'Talleres colaborativos y prototipado con materiales reciclados.',
        'minimal_technology': 'Materiales para prototipar, papel, pizarra',
        'estimated_duration': '180 minutos',
        'workflow_status': 'published',
        'board_stage': 'en_clase',
        'week_slot': 4,
        'planning_markdown': '# Design Thinking\n\n## Fases\n1. Empatizar\n2. Definir\n3. Idear\n4. Prototipar\n5. Probar',
        'iste_standards': ['5a', '6a'],
    },
]

def get_or_create_iste_standards(codes):
    """Obtiene o crea estándares ISTE"""
    standards = []
    for code in codes:
        standard = ISTEStandard.query.filter_by(code=code).first()
        if not standard:
            standard = ISTEStandard(
                code=code,
                description=f'Estándar ISTE {code}'
            )
            db.session.add(standard)
        standards.append(standard)
    db.session.commit()
    return standards


def seed_test_projects():
    """Crea proyectos de prueba"""
    with app.app_context():
        # Verificar si ya existen proyectos
        existing = LearningExperience.query.count()
        if existing > 0:
            print(f'⚠️  Ya existen {existing} proyectos en la base de datos')
            response = input('¿Deseas continuar y agregar más proyectos? (s/n): ')
            if response.lower() != 's':
                return

        created_count = 0
        for project_data in TEST_PROJECTS:
            try:
                # Extraer estándares ISTE
                iste_codes = project_data.pop('iste_standards', [])
                standards = get_or_create_iste_standards(iste_codes)

                # Crear el proyecto
                project = LearningExperience(
                    **project_data,
                    image_file='default.jpg',
                    created_at=datetime.utcnow()
                )
                
                # Asociar estándares
                project.iste_standards = standards
                
                db.session.add(project)
                db.session.flush()

                # Agregar comentarios de ejemplo
                comments_text = [
                    'Excelente proyecto. Los estudiantes aprenden rápido con este enfoque.',
                    'Necesita más claridad en los objetivos de aprendizaje.',
                    'Muy bien estructurado. Recomendado para el ciclo escolar.',
                    'Falta integración con otras áreas del currículo.',
                ]
                
                for i, comment_text in enumerate(comments_text[:2]):
                    comment = Comment(
                        content=comment_text,
                        author=f'Docente {i+1}',
                        learning_experience_id=project.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(comment)

                db.session.commit()
                created_count += 1
                status_icon = '✓'
                print(f'{status_icon} Proyecto creado: {project.title}')

            except Exception as e:
                db.session.rollback()
                print(f'✗ Error creando {project_data.get("title")}: {str(e)}')

        print(f'\n✅ Se crearon {created_count} proyectos de prueba')
        print(f'Total de proyectos en la base de datos: {LearningExperience.query.count()}')


if __name__ == '__main__':
    seed_test_projects()
