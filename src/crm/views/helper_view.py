from src.crm.views.views import MainView

view = MainView()

class HelperView:
    def password_length_helper(self):
        view.wrong_message(
            "Password should be between 8 and 64 characters long."
        )

    def password_helper(self):
        view.wrong_message(
            "Password should be :\n"
            "\t- at least 8 characters long\n"
            "\t- 64 characters long maximum\n"
            "\tcomposed of at least:\n"
            "\t\t- one uppercase letter\n"
            "\t\t- one lowercase letter\n"
            "\t\t- one number"
        )

    def password_confirmation_helper(self):
        view.wrong_message(
            "Password and confirmation password do not match."
        )

    def username_helper(self):
        view.wrong_message(
            "Username should be between 5 and 64 characters long."
        )
