############################################################################
#
# Copyright (C) 2014 Ruben Pollan <meskio@sindominio.net>
# Copyright (C) 2014 tele <tele@rhizomatica.org>
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
"""
rhizomatica roaming checker
"""

from config import *


def purge_inactive_subscribers():
    sub = Subscriber()
    try:
        inactive = sub.get_all_inactive_roaming()
    except SubscriberException as e:
        roaming_log.error("An error ocurred getting the list of inactive: %s" % e)
        return

    for msisdn in inactive:
        try:
            sub.purge(msisdn)
            roaming_log.info("Roaming Subscriber %s purged" % msisdn)
        except SubscriberException as e:
            roaming_log.error("An error ocurred on %s purge: %s" % (msisdn, e))

if __name__ == '__main__':
    purge_inactive_subscribers()
