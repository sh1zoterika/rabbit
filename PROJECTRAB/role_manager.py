# role_manager.py
class RoleManager:
    def __init__(self):
        self.user_roles = {}  # {user_id: set(roles)}

    def assign_role(self, user_id, role):
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        # Проверка на конфликтующие роли
        if role == 'A' and 'C' in self.user_roles[user_id]:
            raise Exception(f"Пользователь {user_id} не может одновременно иметь роли C и A.")
        if role == 'C' and 'A' in self.user_roles[user_id]:
            raise Exception(f"Пользователь {user_id} не может одновременно иметь роли A и C.")
        self.user_roles[user_id].add(role)
        print(f"Роль {role} назначена пользователю {user_id}.")

    def remove_role(self, user_id, role):
        if user_id in self.user_roles and role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            print(f"Роль {role} снята с пользователя {user_id}.")

    def has_role(self, user_id, role):
        return user_id in self.user_roles and role in self.user_roles[user_id]
