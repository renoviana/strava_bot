from mongoengine import connect

from secure import MONGO_URI
from model.strava_activity import StravaActivity
from model.strava_group import StravaGroup


class DbManager:

    def __init__(self, group_id):
        connect(host=MONGO_URI)
        self.group_id = int(group_id)

    def get_strava_group(self) -> StravaGroup:
        """
        Retorna dados de um grupo
        """
        strava_group = StravaGroup.objects(telegram_group_id=self.group_id).first()

        if not strava_group:
            self.add_strava_group()
            strava_group = StravaGroup.objects(telegram_group_id=self.group_id).first()

        return strava_group

    def add_strava_group(self):
        """
        Adiciona grupo do telegram a base de dados
        """
        return StravaGroup(
            telegram_group_id=self.group_id,
            membros={},
            metas={},
            ignored_activities=[],
            segments_ids=[],
            medalhas={"ride": {}},
            cache_data=[],
        ).save()

    def list_strava_activities(self, user_id, first_day, last_day):
        """
        Lista atividades de um usuário
        Args:
            user_id (int): id do usuário
            first_day (datetime): data inicial
            last_day (datetime): data final
        """
        query = {
            "group_id": self.group_id,
            "athlete.id": user_id,
            "start_date_local": {
                "$gte": first_day,
                "$lt": last_day,
            },
        }

        return StravaActivity.objects(__raw__=query).order_by("-start_date_local").all()

    def update_membro(self, user_name, data):
        """
        Atualiza dados de um membro
        Args:
            user_name (str): nome do usuário
            data (dict): dados do usuário
        """
        group = self.get_strava_group()
        group.membros[user_name] = data
        group.save()

    def remove_strava_user(self, user_name):
        """
        Remove usuário do strava
        Args:
            user_name (str): nome do usuário
            user_name_admin (str): nome do admin
        """
        strava_group = self.get_strava_group()
        if user_name not in strava_group.membros:
            return None

        removed_user_id = strava_group.membros[user_name].get("athlete_id")
        strava_group.membros = {
            key: value
            for key, value in strava_group.membros.items()
            if key != user_name
        }

        query = {
            "athlete.id": removed_user_id,
            "group_id": self.group_id,
        }
        StravaActivity.objects(__raw__=query).delete()
        strava_group.save()
        return strava_group.membros

    def update_meta(self, sport_name, km):
        """
        Atualiza meta de algum esporte
        Args:
            sport_name (str): tipo de meta
            km (int): km da meta
        """
        strava_group = self.get_strava_group()
        metas = strava_group.metas

        if km:
            km = int(km)
            metas[sport_name] = km
        else:
            del metas[sport_name]

        strava_group.metas = metas
        strava_group.save()
        return strava_group.metas

    def add_ignore_activity(self, activity_id):
        """
        Ignora atividade
        Args:
            activity_id (str): id da atividade
        """
        strava_group = self.get_strava_group()
        ignored_activities = strava_group.ignored_activities or []
        ignored_activities.append(str(activity_id))
        strava_group.ignored_activities = ignored_activities
        strava_group.save()
        return strava_group.ignored_activities

    def process_activities(self, new_activity_list):
        """
        Processa atividades
        Args:
            new_activity_list (list): lista de atividades
        """
        if not new_activity_list:
            return

        mongo_lista = []
        for activity in new_activity_list:
            activity_dict = activity.copy()
            activity_dict["group_id"] = self.group_id
            activity_dict["activity_type"] = activity_dict["type"]
            activity_dict["activity_id"] = activity_dict["id"]
            activity_dict["activity_map"] = activity_dict["map"]
            del activity_dict["type"]
            del activity_dict["id"]
            del activity_dict["map"]
            mongo_lista.append(StravaActivity(**activity_dict))

        StravaActivity.objects.insert(mongo_lista)

    def remove_activities(self, query):
        """
        Remove atividades
        Args:
            query (dict): query de busca
        """
        StravaActivity.objects(__raw__=query).delete()

    def add_ignored_activity_rank(self, ignored_activities_rank):
        """
        Adiciona atividades ignoradas
        Args:
            ignored_activities_rank (list): lista de atividades ignoradas
        """
        strava_group = self.get_strava_group()
        strava_group.ignored_activities_rank = ignored_activities_rank
        strava_group.save()
