class AltChar:
    def __init__(self):
        # Initialize default values for all attributes
        self.char_name = ""
        self.char_rank = ""
        self.char_level = -10
        self.char_class = ""
        self.char_race = ""
        self.char_sex = ""
        self.char_last_on = ""
        self.char_is_alt = False
        self.char_alts = []
        self.char_join_date = ""
        self.char_promo_date = ""
        self.char_rank_hist = []
        self.char_bday = ""
        self.char_pub_note = ""
        self.char_officer_note = ""
        self.char_custom_note = ""
        self.char_faction = ""
        self.kudos = 0
        self.disc_user = ""
        self.nickname = ""
        self.main_name = ""
    
    def load_from_list(self, data):
        # Dynamically get all attribute names except built-in ones
        fields = [attr for attr in vars(self) if not attr.startswith("__")]

        for i, field in enumerate(fields):
            if i < len(data):
                setattr(self, field, data[i])



    def list_info(self):
        info = vars(self).values()
        return info
    
    