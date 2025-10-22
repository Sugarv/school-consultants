from django.templatetags.static import static
from django.urls import reverse_lazy
from .utils import is_member_of_many
from django.conf import settings


UNFOLD = {
    "SITE_TITLE": "Εφαρμογή συμβούλων εκπαίδευσης",
    "SITE_HEADER": "Εφαρμογή συμβούλων εκπαίδευσης",
    "SITE_URL": "/",
    # "SITE_ICON": lambda request: static("icon.svg"),  # both modes, optimise for 32px height
    # "SITE_ICON": {
    #     "light": lambda request: static("icon-light.svg"),  # light mode
    #     "dark": lambda request: static("icon-dark.svg"),  # dark mode
    # },
    # "SITE_LOGO": lambda request: static("logo.svg"),  # both modes, optimise for 32px height
    # "SITE_LOGO": {
    #     "light": lambda request: static("logo-light.svg"),  # light mode
    #     "dark": lambda request: static("logo-dark.svg"),  # dark mode
    # },
    "SITE_SYMBOL": "speed",  # symbol from icon set
    # "SITE_FAVICONS": [
    #     {
    #         "rel": "icon",
    #         "sizes": "32x32",
    #         "type": "image/svg+xml",
    #         "href": lambda request: static("favicon.svg"),
    #     },
    # ],
    "SHOW_HISTORY": True, # show/hide "History" button, default: True
    "SHOW_VIEW_ON_SITE": False, # show/hide "View on site" button, default: True
    "ENVIRONMENT": "app.utils.environment_callback",
    "DASHBOARD_CALLBACK": "symvouloi.views.dashboard_callback",
    # "THEME": "dark", # Force theme: "dark" or "light". Will disable theme switcher
    "LOGIN": {
        "image": lambda request: static("login-bg.png"),
        # "redirect_after": lambda request: reverse_lazy("admin:APP_MODEL_changelist"),
    },
    "STYLES": [
        lambda request: static("css/style.css"),
    ],
    # "SCRIPTS": [
    #     lambda request: static("js/script.js"),
    # ],
    # "COLORS": {
    #     "font": {
    #         "subtle-light": "107 114 128",
    #         "subtle-dark": "156 163 175",
    #         "default-light": "75 85 99",
    #         "default-dark": "209 213 219",
    #         "important-light": "17 24 39",
    #         "important-dark": "243 244 246",
    #     },
    #     "primary": {
    #         "50": "250 245 255",
    #         "100": "243 232 255",
    #         "200": "233 213 255",
    #         "300": "216 180 254",
    #         "400": "192 132 252",
    #         "500": "168 85 247",
    #         "600": "147 51 234",
    #         "700": "126 34 206",
    #         "800": "107 33 168",
    #         "900": "88 28 135",
    #         "950": "59 7 100",
    #     },
    # },
    # "EXTENSIONS": {
    #     "modeltranslation": {
    #         "flags": {
    #             "en": "🇬🇧",
    #             "fr": "🇫🇷",
    #             "nl": "🇧🇪",
    #         },
    #     },
    # },
    "SIDEBAR": {
        "show_search": False,  # Search in applications and models names
        "show_all_applications": False,  # Dropdown with all applications and models
        "navigation": [
            {
                "title": "Αξιολόγηση",
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": "Αρχική",
                        "icon": "dashboard",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: is_member_of_many(request.user, 'Σύμβουλοι,Επόπτες') or request.user.is_superuser,
                    },
                    {
                        "title": "Εκπαιδευτικοί",
                        "icon": "school",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:symvouloi_teacher_changelist"),
                        "permission": lambda request: is_member_of_many(request.user, 'Σύμβουλοι,Επόπτες') or request.user.is_superuser,
                    },
                    {
                        "title": "Βήματα αξιολόγησης",
                        "icon": "footprint",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:symvouloi_evaluationstep_changelist"),
                        "permission": lambda request: is_member_of_many(request.user, 'Σύμβουλοι,Επόπτες') or request.user.is_superuser,
                    },
                    {
                        "title": "Τύποι βημάτων αξιολόγησης",
                        "icon": "floor",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:symvouloi_evaluationsteptype_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Αναθέσεις εκπ/κών",
                        "icon": "assignment",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:symvouloi_teacherassignment_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Ιστορικό αξιολογήσεων",
                        "icon": "history",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:symvouloi_evaluationdata_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Έλεγχος αξιολόγησης",
                        "icon": "quick_reference_all",
                        "link": reverse_lazy("admin:evaluation_check"),
                        "permission": lambda request: is_member_of_many(request.user, 'Σύμβουλοι,Επόπτες') or request.user.is_superuser,
                    },
                    
                ],
            },
            {
                "title": "Μετακινήσεις",
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": "Ημερολόγιο",
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:metakinhsh_calendar"),
                    },
                    {
                        "title": "Λίστα",
                        "icon": "no_crash",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:metakinhseis_metakinhsh_changelist"),
                        # "badge": "main.badge_callback",
                        # "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Προσθήκη",
                        "icon": "assignment_add",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:metakinhseis_metakinhsh_add"),
                        # "badge": "main.badge_callback",
                        "permission": lambda request: is_member_of_many(request.user, 'Σύμβουλοι,Επόπτες,Γραμματεία') or request.user.is_superuser,
                    },
                    {
                        "title": "Εισαγωγή",
                        "icon": "database_upload",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:metakinhsh_import"),
                        # "badge": "main.badge_callback",
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Ημέρες Γραφείου",
                        "icon": "meeting_room",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:metakinhseis_officeschedule_changelist"),
                        # "badge": "main.badge_callback",
                        "permission": lambda request: 
                            settings.SHOW_OFFICE_DAYS and (is_member_of_many(request.user, 'Σύμβουλοι,Επόπτες,Γραμματεία') or request.user.is_superuser),
                    },

                ],
            },
            {
                "title": "Διαχείριση",
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": "Χρήστες",
                        "icon": "people",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Ομάδες",
                        "icon": "groups",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Καταγραφή",
                        "icon": "frame_inspect",
                        "link": reverse_lazy("admin:admin_logentry_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Διακοπή μίμησης",
                        "icon": "search_off",
                        "link": reverse_lazy("impersonate-stop"),
                        "permission": lambda request: request.user.is_impersonate,
                    },
                ],
            },
        ],
    },
    # "TABS": [
    #     {
    #         "models": [
    #             "app_label.model_name_in_lowercase",
    #         ],
    #         "items": [
    #             {
    #                 "title": _("Your custom title"),
    #                 "link": reverse_lazy("admin:app_label_model_name_changelist"),
    #                 "permission": "sample_app.permission_callback",
    #             },
    #         ],
    #     },
    # ],
}


def environment_callback(request):
    """
    Callback has to return a list of two values represeting text value and the color
    type of the label displayed in top right corner.
    """
    return ["Production", "danger"] # info, danger, warning, success
