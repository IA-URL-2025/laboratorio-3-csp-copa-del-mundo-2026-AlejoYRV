import copy

class WorldCupCSP:
    def __init__(self, teams, groups, debug=False):
        """
        Inicializa el problema CSP para el sorteo del Mundial.
        :param teams: Diccionario con los equipos, sus confederaciones y bombos.
        :param groups: Lista con los nombres de los grupos (A-L).
        :param debug: Booleano para activar trazas de depuración.
        """
        self.teams = teams
        self.groups = groups
        self.debug = debug

        # Las variables son los equipos.
        self.variables = list(teams.keys())

        # El dominio de cada variable inicialmente son todos los grupos.
        self.domains = {team: list(groups) for team in self.variables}

    # Helpers
    def get_team_confederation(self, team):
        return self.teams[team]["conf"]

    def get_team_pot(self, team):
        return self.teams[team]["pot"]

    def _teams_in_group(self, group, assignment):
        """Devuelve la lista de equipos ya asignados a un grupo."""
        return [t for t, g in assignment.items() if g == group]

    # Restricciones
    def is_valid_assignment(self, group, team, assignment):
        """
        Verifica si asignar un equipo a un grupo viola las restricciones.

        Restricción 1 — Tamaño: máximo 4 equipos por grupo.
        Restricción 2 — Bombo único: no puede haber dos equipos del mismo bombo.
        Restricción 3 — Confederación: máximo 1 equipo por confederación,
                         excepto UEFA que permite hasta 2.
        """
        current_teams = self._teams_in_group(group, assignment)
        team_conf = self.get_team_confederation(team)
        team_pot = self.get_team_pot(team)

        # Restricción 1: tamaño máximo del grupo 
        if len(current_teams) >= 4:
            if self.debug:
                print(f"  [INVALID] {team} -> Grupo {group}: grupo lleno ({len(current_teams)}/4)")
            return False

        # Restricción 2: un solo equipo por bombo 
        for t in current_teams:
            if self.get_team_pot(t) == team_pot:
                if self.debug:
                    print(f"  [INVALID] {team} -> Grupo {group}: bombo {team_pot} ya ocupado por {t}")
                return False

        # Restricción 3: confederaciones 
        conf_count = {}
        for t in current_teams:
            c = self.get_team_confederation(t)
            conf_count[c] = conf_count.get(c, 0) + 1

        current_same_conf = conf_count.get(team_conf, 0)

        if team_conf == "UEFA":
            # UEFA: máximo 2 por grupo
            if current_same_conf >= 2:
                if self.debug:
                    print(f"  [INVALID] {team} -> Grupo {group}: UEFA ya tiene {current_same_conf} equipos")
                return False
        else:
            # Resto de confederaciones: máximo 1
            if current_same_conf >= 1:
                if self.debug:
                    print(f"  [INVALID] {team} -> Grupo {group}: {team_conf} ya tiene 1 equipo")
                return False

        if self.debug:
            print(f"  [VALID]   {team} -> Grupo {group}")
        return True

    # Forward Checking

    def forward_check(self, assignment, domains):
        """
        Propagación de restricciones.
        Para cada equipo no asignado, elimina del dominio los grupos
        que ya serían inválidos dada la asignación actual.
        Retorna (True, new_domains) si todo OK, (False, _) si algún dominio queda vacío.
        """
        new_domains = copy.deepcopy(domains)

        for team in self.variables:
            if team in assignment:
                continue

            # Filtrar grupos válidos para este equipo
            valid_groups = [
                g for g in new_domains[team]
                if self.is_valid_assignment(g, team, assignment)
            ]

            if len(valid_groups) == 0:
                if self.debug:
                    print(f"  [FC FAIL] Dominio vacío para {team}")
                return False, new_domains

            new_domains[team] = valid_groups

        return True, new_domains
-
    # Heurística MRV

    def select_unassigned_variable(self, assignment, domains):
        """
        Heurística MRV (Minimum Remaining Values).
        Selecciona el equipo no asignado con el dominio más pequeño
        (menos grupos posibles), lo que reduce el espacio de búsqueda.
        """
        unassigned = [v for v in self.variables if v not in assignment]

        if not unassigned:
            return None

        # Ordenar por tamaño de dominio ascendente; en caso de empate,
        # preferir el que viene primero en la lista (orden estable).
        mrv_team = min(unassigned, key=lambda t: len(domains[t]))

        if self.debug:
            print(f"  [MRV] Seleccionado: {mrv_team} (dominio={domains[mrv_team]})")

        return mrv_team

    # Backtracking

    def backtrack(self, assignment, domains=None):
        """
        Backtracking search con Forward Checking para resolver el CSP.
        """
        if domains is None:
            domains = copy.deepcopy(self.domains)

        # Condición de parada: todos los equipos asignados
        if len(assignment) == len(self.variables):
            return assignment

        # 1. Seleccionar la variable con MRV
        team = self.select_unassigned_variable(assignment, domains)
        if team is None:
            return None

        if self.debug:
            print(f"\n[BACKTRACK] Intentando asignar: {team} "
                  f"({self.get_team_confederation(team)}, Bombo {self.get_team_pot(team)})")
            print(f"  Dominio actual: {domains[team]}")

        # 2. Iterar sobre los grupos posibles en el dominio actual
        for group in domains[team]:
            if self.is_valid_assignment(group, team, assignment):

                # 3. Hacer la asignación
                assignment[team] = group

                if self.debug:
                    print(f"  [ASSIGN] {team} -> Grupo {group}")

                # 4. Forward Checking: propagar restricciones
                ok, new_domains = self.forward_check(assignment, domains)

                if ok:
                    # 5. Llamada recursiva
                    result = self.backtrack(assignment, new_domains)
                    if result is not None:
                        return result

                # 6. Backtrack: deshacer la asignación
                if self.debug:
                    print(f"  [BACKTRACK] Deshaciendo {team} -> Grupo {group}")
                del assignment[team]

        # Ningún grupo funcionó para este equipo
        return None
