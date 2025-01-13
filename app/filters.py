from datetime import datetime
from unfold.contrib.filters.admin import RangeDateForm
from django.contrib import admin
from django.db.models.fields import (
    DateField,
    Field,
)
from django.http import HttpRequest
from typing import Any, Dict, List, Optional, Tuple, Type
from django.contrib.admin.options import ModelAdmin
from django.db.models import Model, QuerySet
from django.core.validators import EMPTY_VALUES
from django.forms import ValidationError
from django.contrib.admin.views.main import ChangeList


def parse_greek_date(date_str):
    # Parse the Greek date format (dd/mm/yyyy)
    day, month, year = date_str.split('/')
    return datetime(int(year), int(month), int(day))


# Rewrite of unfold admin's RangeDateFilter (django-unfold/src/unfold/contrib/filters/admin.py)
# in order to support greek date format
class MyRangeDateFilter(admin.FieldListFilter):
    request = None
    parameter_name = None
    form_class = RangeDateForm
    template = "unfold/filters/filters_date_range.html"

    def expected_parameters(self) -> List[str]:
        return [
            f"{self.parameter_name}_from",
            f"{self.parameter_name}_to",
        ]

    def choices(self, changelist: ChangeList) -> Tuple[Dict[str, Any], ...]:
        return (
            {
                "request": self.request,
                "parameter_name": self.parameter_name,
                "form": self.form_class(
                    name=self.parameter_name,
                    data={
                        self.parameter_name + "_from": self.used_parameters.get(
                            self.parameter_name + "_from", None
                        ),
                        self.parameter_name + "_to": self.used_parameters.get(
                            self.parameter_name + "_to", None
                        ),
                    },
                ),
            },
        )

    def __init__(
        self,
        field: Field,
        request: HttpRequest,
        params: Dict[str, str],
        model: Type[Model],
        model_admin: ModelAdmin,
        field_path: str,
    ) -> None:
        super().__init__(field, request, params, model, model_admin, field_path)
        if not isinstance(field, DateField):
            raise TypeError(
                f"Class {type(self.field)} is not supported for {self.__class__.__name__}."
            )

        self.request = request
        if self.parameter_name is None:
            self.parameter_name = self.field_path

        if self.parameter_name + "_from" in params:
            value = params.pop(self.field_path + "_from")
            value = value[0] if isinstance(value, list) else value

            if value not in EMPTY_VALUES:
                self.used_parameters[self.field_path + "_from"] = value

        if self.parameter_name + "_to" in params:
            value = params.pop(self.field_path + "_to")
            value = value[0] if isinstance(value, list) else value

            if value not in EMPTY_VALUES:
                self.used_parameters[self.field_path + "_to"] = value

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        filters = {}

        value_from = self.used_parameters.get(self.parameter_name + "_from")
        if value_from not in EMPTY_VALUES:
            parsed_date_from = parse_greek_date(value_from)
            filters.update({self.parameter_name + "__gte": parsed_date_from})

        value_to = self.used_parameters.get(self.parameter_name + "_to")
        if value_to not in EMPTY_VALUES:
            parsed_date_to = parse_greek_date(value_to)
            filters.update({self.parameter_name + "__lte": parsed_date_to})

        try:
            return queryset.filter(**filters)
        except (ValueError, ValidationError):
            return None