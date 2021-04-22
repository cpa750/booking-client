import datetime
import string
from random import choice, randint
from timeit import default_timer

import Pyro5.api

from core.strongbundler import StrongBundler
from core.multicaller import *


def get_args():
    import sys
    if len(sys.argv) < 3:
        return False
    else:
        return sys.argv[1], int(sys.argv[2])


args = get_args()
if args:
    nameserver = Pyro5.api.locate_ns(host=args[0], port=args[1])
else:
    nameserver = Pyro5.api.locate_ns()

uri = nameserver.lookup("bookingservice")
proxy = Pyro5.api.Proxy(uri)

multicaller = MultiCaller(proxy)
bundler = StrongBundler(multicaller)

bundler.register_command(multicaller.set_customer)
bundler.register_command(multicaller.make_bookmark)
bundler.register_command(multicaller.update_reservation_end)


def get_strong_bundled_execution_time(iteration: int, caller, no_of_bookmarks):
    username = str(iteration)
    # Getting random username
    name = ''.join(choice(string.ascii_letters) for _ in range(20))
    # Getting a standard 11-digit phone number
    phone_no = str(randint(10000000000, 99999999999))
    # Getting dates
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=1)
    updated_end_date = end_date + datetime.timedelta(days=1)

    start = default_timer()

    caller.queue(multicaller.create_customer, username, name, phone_no)
    caller.queue(multicaller.set_customer, username)
    caller.queue(multicaller.get_all_location_ids)

    for i in range(no_of_bookmarks):
        caller.queue(multicaller.make_bookmark, i + 1)

    caller.queue(multicaller.get_location_details, 1)
    reservation_id = caller.queue(multicaller.make_reservation,
                                  1, start_date, end_date)
    caller.queue(multicaller.update_reservation_end, reservation_id, updated_end_date)
    caller.queue(multicaller.checkout)

    end = default_timer()
    return end - start


def get_weak_bundled_execution_time(iteration: int, caller, no_of_bookmarks):
    username = str(iteration)
    # Getting random username
    name = ''.join(choice(string.ascii_letters) for _ in range(20))
    # Getting a standard 11-digit phone number
    phone_no = str(randint(10000000000, 99999999999))
    # Getting dates
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=1)
    updated_end_date = end_date + datetime.timedelta(days=1)

    start = default_timer()

    caller.create_customer(username, name, phone_no)
    caller.set_customer(username)
    caller.get_all_location_ids()

    for i in range(no_of_bookmarks):
        caller.make_bookmark(i + 1)

    caller.get_location_details(1)
    reservation_id = caller.make_reservation(1, start_date, end_date)
    caller.update_reservation_end(reservation_id, updated_end_date)
    caller.checkout()

    end = default_timer()
    return end - start


def timing_loop(no_of_iterations, timing_func, caller, no_of_bookmarks):
    aggregate_time = 0
    for i in range(no_of_iterations):
        aggregate_time += timing_func(i, caller, no_of_bookmarks)
    return aggregate_time


def get_times(strong, weak, no_of_timings, no_of_iterations, no_of_bookmarks):
    strong_times = []
    weak_times = []
    for i in range(no_of_timings):
        # Resetting the server's database so the same data is always inserted/modified
        proxy.reset_db()
        strong_times.append(timing_loop(
            no_of_iterations, get_strong_bundled_execution_time,
            strong, no_of_bookmarks))
        proxy.reset_db()
        weak_times.append(timing_loop(
            no_of_iterations, get_weak_bundled_execution_time,
            weak, no_of_bookmarks))

    print("Strong Time", "Weak Time", sep=5 * '\t')
    for i in range(len(strong_times)):
        print(strong_times[i], weak_times[i], sep=5 * '\t')
    print("Strong min/max/avg:")
    print(min(strong_times), max(strong_times), sum(strong_times) / len(strong_times))
    print("Weak min/max/avg:")
    print(min(weak_times), max(weak_times), sum(weak_times) / len(weak_times))


print("Small no. of bookmarks: ")
get_times(bundler, proxy, 10, 1000, 2)
print("Large number of bookmarks: ")
get_times(bundler, proxy, 10, 1000, 10)
