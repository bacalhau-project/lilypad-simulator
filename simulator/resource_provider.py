from utils import *
from machine import Machine
from service_provider import ServiceProvider
from solver import Solver
from match import Match
from smart_contract import SmartContract
from result import Result
import logging
import os


class ResourceProvider(ServiceProvider):
    def __init__(self, public_key: str):
        # machines maps CIDs -> machine metadata
        super().__init__(public_key)
        self.logger = logging.getLogger(f"Resource Provider {self.public_key}")
        logging.basicConfig(filename=f'{os.getcwd()}/local_logs', filemode='w', level=logging.DEBUG)
        self.machines = {}
        self.solver_url = None
        self.solver = None
        self.smart_contract = None
        self.current_deals = {}  # maps deal id to deals
        self.current_job_running_times = {}  # maps deal id to how long the resource provider has been running the job
        self.deals_finished_in_current_step = []
        self.current_matched_offers = []

    def get_solver(self):
        return self.solver

    def get_smart_contract(self):
        return self.smart_contract

    def connect_to_solver(self, url: str, solver: Solver):
        self.solver_url = url
        self.solver = solver
        self.solver.subscribe_event(self.handle_solver_event)
        self.solver.get_local_information().add_resource_provider(self)

    def connect_to_smart_contract(self, smart_contract: SmartContract):
        self.smart_contract = smart_contract
        smart_contract.subscribe_event(self.handle_smart_contract_event)

    def add_machine(self, machine_id: CID, machine: Machine):
        self.machines[machine_id.hash] = machine

    def remove_machine(self, machine_id):
        self.machines.pop(machine_id)

    def get_machines(self):
        return self.machines

    def create_resource_offer(self):
        pass

    def _agree_to_match(self, match: Match):
        timeout_deposit = match.get_data()['timeout_deposit']
        tx = Tx(sender=self.get_public_key(), value=timeout_deposit)
        self.get_smart_contract().agree_to_match(match, tx)

    def handle_solver_event(self, event):
        self.logger.info(f"have solver event {event.get_name(), event.get_data().get_id()}")
        if event.get_name() == 'match':
            match = event.get_data()
            if match.get_data()['resource_provider_address'] == self.get_public_key():
                self.current_matched_offers.append(match)

    def handle_smart_contract_event(self, event):
        self.logger.info(f"have smart contract event {event.get_name(), event.get_data().get_id()}")
        if event.get_name() == 'deal':
            deal = event.get_data()
            deal_data = deal.get_data()
            deal_id = deal.get_id()
            if deal_data['resource_provider_address'] == self.get_public_key():
                self.current_deals[deal_id] = deal
                self.current_job_running_times[deal_id] = 0

    def post_result(self, result: Result, tx: Tx):
        self.get_smart_contract().post_result(result, tx)

    def create_result(self, deal_id):
        self.logger.info(f"posting the result for deal {deal_id}")
        result = Result()
        result.add_data('deal_id', deal_id)
        instruction_count = 1
        result.add_data('instruction_count', instruction_count)
        result.set_id()
        result.add_data('result_id', result.get_id())
        cheating_collateral_multiplier = self.current_deals[deal_id].get_data()['cheating_collateral_multiplier']
        cheating_collateral = cheating_collateral_multiplier * int(instruction_count)
        tx = Tx(sender=self.get_public_key(), value=cheating_collateral)
        return result, tx

    def update_finished_deals(self):
        # remove finished deals from list of current deals and running jobs
        for deal_id in self.deals_finished_in_current_step:
            del self.current_deals[deal_id]
            del self.current_job_running_times[deal_id]
        # clear list of deals finished in current step
        self.deals_finished_in_current_step.clear()

    def handle_completed_job(self, deal_id):
        result, tx = self.create_result(deal_id)
        self.post_result(result, tx)
        self.deals_finished_in_current_step.append(deal_id)

    def update_job_running_times(self):
        for deal_id, running_time in self.current_job_running_times.items():
            self.current_job_running_times[deal_id] += 1
            expected_running_time = self.current_deals[deal_id].get_data()['actual_honest_time_to_completion']
            if self.current_job_running_times[deal_id] >= expected_running_time:
                self.handle_completed_job(deal_id)

        self.update_finished_deals()

    def resource_provider_loop(self):
        for match in self.current_matched_offers:
            self._agree_to_match(match)
        self.update_job_running_times()
        self.current_matched_offers.clear()


# todo when handling events, add to list to be managed later, i.e. don't start signing stuff immediately













