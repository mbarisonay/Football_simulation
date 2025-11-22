import sqlite3
import sys
import os

# Veritabanı yolunu bulma karmaşasını çözer
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'Football_Simulation', 'database',
                       'football_sim.db')


# Eğer yukarıdaki path çalışmazsa, senin projendeki sabit yolu kullan:
# db_path = "C:/Users/mbari/source/repos/Football_simulation/database/football_sim.db"

class Team:
    def __init__(self, team_name, season):
        self.name = team_name
        self.season = season
        self.stats = {
            'Overall': 0,
            'Attack': 0,
            'Midfield': 0,
            'Defense': 0,
            'Pace': 0
        }
        self.calculate_stats(db_path)

    def calculate_stats(self, db_file):
        """Veritabanından oyuncuları çekip takım gücünü hesaplar"""
        try:
            conn = sqlite3.connect("database/football_sim.db")  # Göreceli yol
            cursor = conn.cursor()

            # ML modelini eğitirken kullandığımız feature'ların aynısını çekmeliyiz!
            query = """
            SELECT 
                AVG(Overall),
                AVG(Finishing),      -- Attack temsili
                AVG(ShortPassing),   -- Midfield temsili
                AVG(StandingTackle), -- Defense temsili
                AVG(SprintSpeed)     -- Pace temsili
            FROM player_stats
            WHERE Team = ? AND Season = ?
            """

            cursor.execute(query, (self.name, self.season))
            result = cursor.fetchone()
            conn.close()

            if result and result[0] is not None:
                self.stats['Overall'] = result[0]
                self.stats['Attack'] = result[1]
                self.stats['Midfield'] = result[2]
                self.stats['Defense'] = result[3]
                self.stats['Pace'] = result[4]
            else:
                print(f"⚠️ Uyarı: {self.name} ({self.season}) için veri bulunamadı. Varsayılan değerler atandı.")
                # Çökmemesi için ortalama değerler
                self.stats = {k: 70 for k in self.stats}

        except Exception as e:
            print(f"Veritabanı Hatası: {e}")
            self.stats = {k: 70 for k in self.stats}

    def get_ml_features(self):
        return self.stats