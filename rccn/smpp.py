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
"""
rhizomatica roaming checker
"""

from config import *
import smpplib.client
from util.dict import TimedDict


roaming = TimedDict()


def smpp_handler(pdu):
    if pdu.command != 'alert_notification':
        return

    imsi = pdu.source_addr
    if imsi not in roaming:
        update_subscriber(imsi)
    roaming[imsi] = True


def update_subscriber(imsi):
    numbering = Numbering()
    sub = Subscriber()
    try:
        msisdn = sub.get_local_msisdn(imsi)
        if len(msisdn) == 11:
            number = msisdn
        else:
            number = numbering.get_msisdn_from_imsi(imsi)

        if current_bts_is_updated(imsi, number):
            return

        if numbering.is_number_local(msisdn):
            update_local_subscriber(imsi, number)
        else:
            update_foreign_subscriber(imsi, number, msisdn)

    except NumberingException as e:
        roaming_log.debug("Couldn't retrieve msisdn from the imsi: %s" % e)
    except SubscriberException as e:
        roaming_log.error("An error ocurred adding the roaming number %s: %s" %
                          (number, e))


def current_bts_is_updated(imsi, number):
    numbering = Numbering()
    pg_hlr_current_bts = numbering.get_current_bts(number)
    rk_hlr_current_bts = numbering.get_bts_distributed_hlr(
        str(imsi), 'current_bts')
    return pg_hlr_current_bts == rk_hlr_current_bts


def update_local_subscriber(imsi, number):
    roaming_log.info(
        'Subscriber %s is back at home_bts, update location' % msisdn)
    sub.update_location(imsi, number, True)


def update_foreign_subscriber(imsi, number, msisdn):
    roaming_log.info('Subscriber %s in roaming, update location' % number)
    if len(msisdn) == 5:
        sub.update(msisdn, "roaming number", number)
        roaming_log.info('Send roaming welcome message to %s' % number)
        send_welcome_sms(number)
    else:
        sub.update_location(imsi, number, False)


def send_welcome_sms(number):
    try:
        sms = SMS()
        sms.send(smsc_shortcode, number, sms_welcome_roaming)
    except SMSException as e:
        roaming_log.error("An error ocurred sending welcome sms to %s: %s" %
                          (number, e))


if __name__ == '__main__':
    # TODO: port number? is it str or int? add it to 'config_values.py'
    client = smpplib.client.Client('127.0.0.1', '2772')
    client.set_message_received_handler(smpp_handler)
    client.connect()
    client.bind_transceiver(system_id='login', password='secret')
    client.listen()
