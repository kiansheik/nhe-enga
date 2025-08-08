# # Make a sqlite3 db locally to store the tupi_only data and keep track of what still needs to be translated
# with sqlite3.connect(DB_PATH) as conn:
#     c = conn.cursor()
#     c.execute(
#         """
#     CREATE TABLE IF NOT EXISTS tupi_only (
#         id INTEGER PRIMARY KEY,
#         vid INTEGER,
#         first_word TEXT,
#         definition TEXT,
#         gloss_language TEXT,
#         gloss TEXT,
#         human_verified INTEGER DEFAULT 0
#     )
#     """
#     )
#     c.execute("CREATE INDEX IF NOT EXISTS idx_vid ON tupi_only(vid)")
#     c.execute("CREATE INDEX IF NOT EXISTS idx_first_word ON tupi_only(first_word)")
#     c.execute(
#         "CREATE INDEX IF NOT EXISTS idx_gloss_language ON tupi_only(gloss_language)"
#     )
#     c.execute("CREATE INDEX IF NOT EXISTS idx_gloss ON tupi_only(gloss)")
#     c.execute(
#         "CREATE INDEX IF NOT EXISTS idx_human_verified ON tupi_only(human_verified)"
#     )
# The following file will be an interface to interact with the tupi_only database.
import os
import sqlite3

DB_PATH = os.path.abspath("/Users/kian/code/nhe-enga/translate/tupi_only.db")


class NavarroDB:
    def __init__(self, db_path=DB_PATH):
        """Initialize the NavarroDB object."""
        self.db_path = db_path

    def create_table(self):
        with sqlite3.connect(self.db_path) as self.conn:
            self.cursor = self.conn.cursor()
            """Create the tupi_only table if it doesn't exist."""
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tupi_only (
                    id INTEGER PRIMARY KEY,
                    vid INTEGER,
                    first_word TEXT,
                    definition TEXT,
                    gloss_language TEXT,
                    gloss TEXT,
                    human_verified INTEGER DEFAULT 0
                )
                """
            )
            self.conn.commit()

    # search for word in the tupi_only table
    def search_word(self, word, classname=None):
        def_search = ""
        if classname:
            if classname == "noun":
                def_search = "(s.)"
            elif classname == "postposition":
                def_search = "(posp.)"
            elif classname == "adverb":
                def_search = ["(adv.)", "(conj.)"]
            elif "pronoun" in classname:
                def_search = "pron."
        with sqlite3.connect(self.db_path) as self.conn:
            self.cursor = self.conn.cursor()
            query = (
                """
            SELECT
              vid,
              first_word,
              definition,
              gloss_language,
              GROUP_CONCAT(gloss, ', ') AS glosses
            FROM
              tupi_only
            WHERE
              first_word = ?
            """
                + (("AND (" +
                    (" OR ".join([f" definition LIKE ? " for _ in def_search])
                    if type(def_search) is list
                    else f" definition LIKE ?") + ")")
                    if def_search
                    else ""
                )+ """ GROUP BY
              vid, first_word, definition, gloss_language
            """
            )
            params = [word] + (
                (
                    [f"%{x}%" for x in def_search]
                    if type(def_search) is list
                    else [f"%{def_search}%"]
                )
                if def_search
                else []
            )
            try:
                # print(f"Executing query: {query} with params: {params}")
                self.cursor.execute(query, params)
                results = self.cursor.fetchall()
            except sqlite3.Error as e:
                print(f"Error executing query: \n{query}\n with params \n{params}\n")
                print(f"Error fetching data: {e}")
                breakpoint()

            vids = set(row[0] for row in results)
            # reduce vid languages into single TupiVerbete objects and return a list of them
            tupi_verbetes = []
            for vid in vids:
                first_word = None
                definition = None
                english_glosses = ""
                portuguese_glosses = ""
                for row in results:
                    if row[0] == vid:
                        if not first_word:
                            first_word = row[1]
                        if not definition:
                            definition = row[2]
                        if row[3].strip() == "en":
                            english_glosses = row[4]
                        elif row[3].strip() == "pt":
                            portuguese_glosses = row[4]
                tupi_verbetes.append(
                    TupiVerbete(
                        first_word,
                        definition=definition,
                        english_glosses=english_glosses,
                        portuguese_glosses=portuguese_glosses,
                    )
                )
            return tupi_verbetes if tupi_verbetes else []


class TupiVerbete:
    def __init__(
        self, verbete, definition="", english_glosses="", portuguese_glosses=""
    ):
        """Initialize a TupiVerbete object."""
        self.verbete = verbete
        self.definition = definition
        self.english_glosses_string = english_glosses
        self.portuguese_glosses_string = portuguese_glosses
        self.english_glosses = [x.strip() for x in english_glosses.split(",")]
        self.portuguese_glosses = [x.strip() for x in portuguese_glosses.split(",")]

    def __repr__(self):
        return f"{self.verbete} - {self.definition} [EN: {self.english_glosses_string}] [PT: {self.portuguese_glosses_string}]"


if __name__ == "__main__":
    import sys

    db = NavarroDB()
    # Example usage
    word = sys.argv[1] if len(sys.argv) > 1 else "ko'yré"
    tupi_verbete = db.search_word(
        word, classname=sys.argv[2] if len(sys.argv) > 2 else None
    )
    if tupi_verbete:
        print(tupi_verbete)
    else:
        print(f"No results found for {word}.")
