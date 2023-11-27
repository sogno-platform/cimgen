from datetime import date, datetime, time
from ..utils.datatypes import Primitive
from ..utils.profile import Profile
from .enum import *

String = Primitive(name="String",type=str, profiles=[Profile.EQBD, Profile.OP, Profile.SSH, Profile.EQ, Profile.DY, Profile.DL, Profile.SV, Profile.SC, ])