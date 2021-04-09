import datetime
import string
from random import choice, randint
from timeit import default_timer

import Pyro5.api

from core.strongbundler import StrongBundler
from core.multicaller import *

nameserver = Pyro5.api.locate_ns()
uri = nameserver.lookup("bookingservice")
proxy = Pyro5.api.Proxy(uri)

multicaller = MultiCaller(proxy)
bundler = StrongBundler(multicaller)

bundler.register_command(multicaller.set_customer)
bundler.register_command(multicaller.make_bookmark)
bundler.register_command(multicaller.update_reservation_end)


def get_strong_bundled_execution_time(iteration: int, caller):
    username = str(iteration)
    # Getting random username
    name = ''.join(choice(string.ascii_letters) for _ in range(20))
    # Getting a standard 11-digit phone number
    phone_no = str(randint(10000000000, 99999999999))

    start = default_timer()

    caller.queue(multicaller.create_customer, username, name, phone_no)
    caller.queue(multicaller.set_customer, username)
    caller.queue(multicaller.get_all_location_ids)
    caller.queue(multicaller.make_bookmark, 1)
    caller.queue(multicaller.make_bookmark, 2)
    caller.queue(multicaller.get_location_details, 1)
    reservation_id = caller.queue(multicaller.make_reservation,
                                  1, datetime.datetime.now(), datetime.datetime.now())
    caller.queue(multicaller.update_reservation_end, reservation_id, datetime.datetime.now())
    caller.queue(multicaller.checkout)

    end = default_timer()
    return end - start


def get_weak_bundled_execution_time(iteration: int, caller):
    username = str(iteration)
    # Getting random username
    name = ''.join(choice(string.ascii_letters) for _ in range(20))
    # Getting a standard 11-digit phone number
    phone_no = str(randint(10000000000, 99999999999))

    start = default_timer()

    caller.create_customer(username, name, phone_no)
    caller.set_customer(username)
    caller.get_all_location_ids()
    caller.make_bookmark(1)
    caller.make_bookmark(2)
    caller.get_location_details(1)
    reservation_id = caller.make_reservation(1, datetime.datetime.now(),
                                             datetime.datetime.now())
    caller.update_reservation_end(reservation_id, datetime.datetime.now())
    caller.checkout()

    end = default_timer()
    return end - start


def timing_loop(no_of_iterations, timing_func, caller):
    aggregate_time = 0
    for i in range(no_of_iterations):
        aggregate_time += timing_func(i, caller)
    return aggregate_time


print("Starting timing...")
# Resetting the server's database so the same data is always inserted/modified
proxy.reset_db()
print(timing_loop(1000, get_strong_bundled_execution_time, bundler))
proxy.reset_db()
print(timing_loop(1000, get_weak_bundled_execution_time, proxy))
