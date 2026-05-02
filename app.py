import os

from flask import Flask

from config import CONFIG_BY_ENV
from extensions import csrf, db, migrate
from models import (
    Comment,
    ISTEStandard,
    LearningExperience,
    LearningExperienceEvaluation,
    LearningExperienceEvaluationScore,
    LearningExperienceRequirement,
    LearningExperienceRubric,
    Material,
    RubricBankItem,
    User,
)
from routes import main_bp, seed_iste_standards, seed_rubric_bank_items


def _get_config_class():
    app_env = os.environ.get('APP_ENV', 'development').lower()
    return CONFIG_BY_ENV.get(app_env, CONFIG_BY_ENV['development'])


def _validate_runtime_config(app):
    app_env = os.environ.get('APP_ENV', 'development').lower()
    if app_env == 'production' and not app.config.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY must be set when APP_ENV=production.')


def create_app():
    app = Flask(__name__)
    app.config.from_object(_get_config_class())
    _validate_runtime_config(app)

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(main_bp)

    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    @app.cli.command('seed-reference-data')
    def seed_reference_data_command():
        seed_iste_standards()
        seed_rubric_bank_items()
        print('Reference data seeded successfully.')

    @app.cli.command('create-user')
    def create_user_command():
        import click

        full_name = click.prompt('Nombre completo').strip()
        email = click.prompt('Email').strip().lower()
        password = click.prompt('Contrasena', hide_input=True, confirmation_prompt=True)
        role = click.prompt('Rol (admin/teacher)', default='teacher').strip().lower()

        if role not in {'admin', 'teacher'}:
            raise click.ClickException('Rol invalido. Usa admin o teacher.')

        if User.query.filter(db.func.lower(User.email) == email).first():
            raise click.ClickException('Ya existe un usuario con ese email.')

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Usuario creado: {email} ({role})')

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)