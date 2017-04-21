from Models import Rubric
from Models import Project
from Models import Category
from Models import Level
import datetime

class Template():
    
    def __init__(self, nickname = "", scorepadDB =None):
        self.scorepadDB = scorepadDB
        self.owner_nick = nickname
        
    def save_template(self):
        
        today = datetime.datetime.now()
        
        rubric = Rubric(None, "Music", "Sample", "Music Rubric",1,"sample","",1)
        self.scorepadDB.insert_rubric(rubric)
        rubric_id = self.scorepadDB.query_maxrubric()
        
        category = Category(None, "Song", rubric_id,"",25)
        level0 = Level(None, "Exemplary","Song relates to genre", None, rubric_id,"",4)
        level1 = Level(None, "Proficient","Song loosely relates to genre", None, rubric_id,"",3)
        level2 = Level(None, "Developing","Song doesn't relate to genre", None, rubric_id,"",2)
        level3 = Level(None, "Unsatisfactory","No song chosen", None, rubric_id,"",1)
        
        levels = [level0, level1, level2, level3]
        self.scorepadDB.insert_criteria(category, levels)
        
        category = Category(None, "Presentation", rubric_id,"",25)
        level0 = Level(None, "Exemplary","Song is explained.Tied well to genre.", None, rubric_id,"",4)
        level1 = Level(None, "Proficient","Song explained but not tied well to \
                        genre/assignment.", None, rubric_id,"",3)
        level2 = Level(None, "Developing","Vague explanation given.", None, rubric_id,"",2)
        level3 = Level(None, "Unsatisfactory","No historical context given.", None, rubric_id,"",1)
        levels = []
        levels = [level0, level1, level2, level3]
        self.scorepadDB.insert_criteria(category, levels)
        
        category = Category(None, "Performance", rubric_id,"",25)
        level0 = Level(None, "Exemplary","Taken seriously. Performed well", None, rubric_id,"",4)
        level1 = Level(None, "Proficient","Performed well with some mistakes", None, rubric_id,"",3)
        level2 = Level(None, "Developing","Not taken very seriously", None, rubric_id,"",2)
        level3 = Level(None, "Unsatisfactory","Weak performance", None, rubric_id,"",1)
        levels = []
        levels = [level0, level1, level2, level3]
        self.scorepadDB.insert_criteria(category, levels)
        
        category = Category(None, "Effort", rubric_id,"",25)
        level0 = Level(None, "Exemplary","Went above and beyond for effort", None, rubric_id,"",4)
        level1 = Level(None, "Proficient","Put significant effort", None, rubric_id,"",3)
        level2 = Level(None, "Developing","Effort put is only asked in class", None, rubric_id,"",2)
        level3 = Level(None, "Unsatisfactory","No effort put in", None, rubric_id,"",1)
        levels = []
        levels = [level0, level1, level2, level3]
        self.scorepadDB.insert_criteria(category, levels)
        
        project = Project(None, "My song", "Sample", "Great Song","Music I",\
                          str(unicode(today.replace(microsecond=0))), 1, 1,rubric_id,"sample","",0)
        
        print project.subject
        self.scorepadDB.insert_project(project)

        
        rubric = Rubric(None, "Art", "Sample", "Art Rubric",1,"sample","",1)
        self.scorepadDB.insert_rubric(rubric)
        rubric_id = self.scorepadDB.query_maxrubric()
        
        category = Category(None, "Creativity", rubric_id,"",33.3333)
        level0 = Level(None, "Exemplary","Generating many ideas", None, rubric_id,"",5)
        level1 = Level(None, "Proficient","Based his or her work on someone else's idea", None, rubric_id,"",4)
        level2 = Level(None, "Developing","Lacked originality", None, rubric_id,"",3)
        level3 = Level(None, "Unsatisfactory","No evidence of trying anything unusual", None, rubric_id,"",2)
        levels = []
        levels = [level0, level1, level2, level3]
        self.scorepadDB.insert_criteria(category, levels)
        
        category = Category(None, "Effort", rubric_id,"",33.3333)
        level0 = Level(None, "Exemplary","Gave it effort far beyond that required", None, rubric_id,"",5)
        level1 = Level(None, "Proficient","The student work hard and completed the project", None, rubric_id,"",4)
        level2 = Level(None, "Developing","Chose an easy project and did it indifferently", None, rubric_id,"",3)
        level3 = Level(None, "Unsatisfactory","Completed with minimum effort", None, rubric_id,"",2)
        levels = []
        levels = [level0, level1, level2, level3]
        self.scorepadDB.insert_criteria(category, levels)
        
        category = Category(None, "Craftsmanship/Skill", rubric_id,"",33.3333)
        level0 = Level(None, "Exemplary","The artwork was beautiful and patiently done", None, rubric_id,"",5)
        level1 = Level(None, "Proficient","Lacks the finishing touches", None, rubric_id,"",4)
        level2 = Level(None, "Developing","The student showed average craftsmanship", None, rubric_id,"",3)
        level3 = Level(None, "Unsatisfactory","The student showed below average craftsmanship", None, rubric_id,"",2)
        levels = []
        levels = [level0, level1, level2, level3]
        self.scorepadDB.insert_criteria(category, levels)
        
        project2 = Project(None, "My Mosaic", "Sample", "Art Project","Art Stud I",\
                          str(unicode(today.replace(microsecond=0))), 0, 1,rubric_id,"sample","",0)
        
        self.scorepadDB.insert_project(project2)
