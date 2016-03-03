############################################################################
#
# Copyright (C) 2016 Ruben Pollan <meskio@sindominio.net>
#
# RCCN is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RCCN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from time import time
from collections import namedtuple
from UserDict import UserDict


"""
Default timeout in seconds
"""
TIMEOUT = 300


class TimedDict(UserDict):
    """
    Dict with timeout for values

    >>> mydict = TimeDict(timeout=20)
    >>> mydict["key"] = "value"
    >>> "key" in mydict
    True
    >>> mydict["key"]
    "value"
    >>> time.sleep(20)
    >>> mydict["key"]
    KeyError: "key"
    """

    TimedValue = namedtuple('TimedValue', ['value', 'date'])

    def __init__(self, *args, **kwargs):
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
        else:
            self.timeout = TIMEOUT
        UserDict.__init__(self, *args, **kwargs)

    def __setitem__(self, key, value):
        data = self.TimedValue(value, time())
        UserDict.__setitem__(self, key, data)

    def __getitem__(self, key):
        data = UserDict.__getitem__(self, key)
        if data.date + self.timeout < time():
            UserDict.__delitem__(self, key)
            raise KeyError(key)
        return data.value

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False
