from unfold.sites import UnfoldAdminSite

from .forms import LoginForm


class SymvouloiAdminSite(UnfoldAdminSite):
  pass
  # login_form = LoginForm


symvouloi_admin_site = SymvouloiAdminSite()