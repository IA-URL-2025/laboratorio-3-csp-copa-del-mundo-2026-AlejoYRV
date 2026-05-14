import copy


class WorldCupCSP:
    def __init__(self, teams, groups, debug=False):
        self.teams = teams
        self.groups = groups
        self.debug = debug
        self.variables = list(teams.keys())
        self.domains = {team: list(groups) for team in self.variables}

    def get_team_confederation(self, team):
        return self.teams[team]["conf"]

    def get_team_pot(self, team):
        return self.teams[team]["pot"]

    def _teams_in_group(self, group, assignment):
        return [t for t, g in assignment.items() if g == group]

    def is_valid_assignment(self, group, team, assignment):
        current_teams = self._teams_in_group(group, assignment)
        team_conf = self.get_team_confederation(team)
        team_pot = self.get_team_pot(team)

        if len(current_teams) >= 4:
            return False

        for t in current_teams:
            if self.get_team_pot(t) == team_pot:
                return False

        conf_count = {}
        for t in current_teams:
            c = self.get_team_confederation(t)
            conf_count[c] = conf_count.get(c, 0) + 1

        current_same_conf = conf_count.get(team_conf, 0)

        if team_conf == "UEFA":
            if current_same_conf >= 2:
                return False
        else:
            if current_same_conf >= 1:
                return False

        return True

    def forward_check(self, assignment, domains):
        new_domains = copy.deepcopy(domains)

        for team in self.variables:
            if team in assignment:
                continue

            valid_groups = [
                g for g in new_domains[team]
                if self.is_valid_assignment(g, team, assignment)
            ]

            new_domains[team] = valid_groups

            if len(valid_groups) == 0:
                return False, new_domains

        return True, new_domains

    def select_unassigned_variable(self, assignment, domains):
        unassigned = [v for v in self.variables if v not in assignment]

        if not unassigned:
            return None

        return min(unassigned, key=lambda t: len(domains[t]))

    def backtrack(self, assignment, domains=None):
        if domains is None:
            domains = copy.deepcopy(self.domains)

        if len(assignment) == len(self.variables):
            return assignment

        team = self.select_unassigned_variable(assignment, domains)
        if team is None:
            return None

        for group in domains[team]:
            if self.is_valid_assignment(group, team, assignment):
                assignment[team] = group

                ok, new_domains = self.forward_check(assignment, domains)

                if ok:
                    result = self.backtrack(assignment, new_domains)
                    if result is not None:
                        return result

                del assignment[team]

        return None
