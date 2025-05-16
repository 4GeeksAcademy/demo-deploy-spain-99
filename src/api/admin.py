
import os
from flask_admin import Admin
from .models import db, User, TokenBlockedList, People, Planet, Favorite
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from wtforms.fields import SelectField, PasswordField
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy import Enum, Boolean
from typing import List, Dict, Type
import inspect


class FavoriteView(ModelView):
    column_display_pk = True
    form_ajax_refs = {
        'user': {
            'fields': ['fullname']
        }}
    form_ajax_refs = {
        'planet': {
            'fields': ['name']
        }, }
    form_ajax_refs = {
        'people': {
            'fields': ['name']
        }
    }


class CustomModelView(ModelView):
    """
    A ModelView that automatically handles foreign key relationships
    for any SQLAlchemy model.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize all list attributes
        self._init_view_attributes()

    def _init_view_attributes(self):
        """Ensure all list attributes are properly initialized"""
        self.form_columns = getattr(self, 'form_columns', []) or []
        self.column_list = getattr(
            self, 'column_list', []) or self._get_model_properties()
        self.column_details_list = getattr(
            self, 'column_details_list', []) or self.column_list
        self.form_excluded_columns = getattr(
            self, 'form_excluded_columns', [])
        self.column_display_all_relations = True
        self.column_display_pk = True
        self.form_ajax_refs = {}

    def scaffold_form(self):
        form_class = super().scaffold_form()

        # Ensure _unbound_fields exists
        if not hasattr(form_class, '_unbound_fields') or form_class._unbound_fields is None:
            form_class._unbound_fields = []

        # Process all mapper properties
        for name, prop in self.model.__mapper__.attrs.items():
            if isinstance(prop, RelationshipProperty):
                self._process_relationship(name, prop, form_class)

        return form_class

    def _process_relationship(self, name: str, prop: RelationshipProperty, form_class):
        """Handle relationship properties with all safety checks"""
        # Ensure form_columns exists
        if not hasattr(self, 'form_columns') or self.form_columns is None:
            self.form_columns = []

        # Add to form columns if not present
        if name not in self.form_columns:
            self.form_columns.append(name)

        # Safely get existing fields
        existing_fields = []
        if hasattr(form_class, '_unbound_fields') and form_class._unbound_fields is not None:
            existing_fields = [
                field[0] for field in form_class._unbound_fields if field and len(field) > 0]

        # Only add if not already present
        if name not in existing_fields:
            remote_model = prop.mapper.class_
            field = SelectField(
                name,
                widget=Select2Widget(),
                choices=self._get_choices_for_model(remote_model),
                validate_choice=False
            )

            # Initialize _unbound_fields if needed
            if not hasattr(form_class, '_unbound_fields') or form_class._unbound_fields is None:
                form_class._unbound_fields = []

            form_class._unbound_fields.append((name, field))

    def _get_choices_for_model(self, model):
        """Safe choice generation with error handling"""
        try:
            with self.session.no_autoflush:
                items = model.query.order_by(model.id).all()
                # Empty option
                choices = [(None, f"Select {model.__name__}...")]
                choices.extend([(item.id, repr(item)) for item in items])
                return choices
                # return [(item.id, repr(item)) for item in items]

        except Exception as e:
            # current_app.logger.error(f"Error generating choices for {model}: {str(e)}")
            print(f"Error generating choices for {model}: {str(e)}")
            return []

    def _get_model_properties(self):
        """Get all properties of the model"""
        return [getattr(self.model, name) for name in dir(self.model)
                if not name.startswith('_')]

    def _is_foreign_key_column(self, prop):
        """Check if a property is a foreign key column"""
        return hasattr(prop, 'property') and isinstance(prop.property, ForeignKey)

    def _process_foreign_key_column(self, prop, form_class):
        """Process a foreign key column"""
        # Find the corresponding relationship if it exists
        rel_name = None
        for name, rel in self.model.__mapper__.relationships.items():
            if rel.target == prop.property.mapper.class_:
                rel_name = name
                break

        field_name = prop.key
        remote_model = prop.property.mapper.class_

        # Only process if there isn't already a relationship field
        if rel_name not in form_class._unbound_fields:
            form_class._unbound_fields.append((
                field_name,
                SelectField(
                    field_name,
                    widget=Select2Widget(),
                    choices=self._get_choices_for_model(remote_model)
                )
            ))

            if field_name not in self.form_columns:
                if not hasattr(self, 'form_columns'):
                    self.form_columns = []
                self.form_columns.append(field_name)

    def on_model_change(self, form, model, is_created):
        """Handle any special processing when a model is changed"""
        super().on_model_change(form, model, is_created)


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    # Add your models here, for example this is how we add a the User model to the admin

    # admin.add_view(ModelView(User, db.session))
    with app.app_context():
        admin.add_view(ModelView(User, db.session))
        admin.add_view(ModelView(TokenBlockedList, db.session))
        admin.add_view(ModelView(People, db.session))
        admin.add_view(ModelView(Planet, db.session))
        admin.add_view(CustomModelView(Favorite, db.session))

    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))
