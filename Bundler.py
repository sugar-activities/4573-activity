from Models import *
import logging

class Bundler():
    
    def bundle_project(self,project):
        
        project_bundle = "Project|" + str(project.project_id)+"|"+project.title+"|"+\
                        project.author+"|"+project.description+"|"+project.subject+"|"+\
                        str(project.publish_date)+"|"+\
                        str(project.is_owned) + "|"+str(project.is_shared)+"|"+\
                        str(project.rubric_id) +"|"+project.xo_name+"|"+\
                        project.project_sha + "|"+str(project.total_score)
        
        logging.debug(project_bundle)
                        
        return project_bundle
    
    def bundle_rubric(self,rubric):
        
        rubric_bundle = "Rubric|" + str(rubric.rubric_id)+"|"+rubric.title+"|"+\
                        rubric.author+"|"+rubric.description+"|"+\
                        str(rubric.is_predefined) +"|"+rubric.xo_name +"|"+\
                        rubric.rubric_sha+"|"+str(rubric.enable_points)
        
        logging.debug(rubric_bundle)
                        
        return rubric_bundle
    
    def bundle_category(self, categories):
        
        categorylist = []
        for category in categories:
            bundle = "Category|" + str(category.category_id)+"|"+category.name+"|"+\
                str(category.rubric_id) +"|"+\
                category.category_sha +"|"+str(category.percentage)
            categorylist.append(bundle)
            logging.debug(bundle)
        return categorylist
    
    def bundle_level(self, levels):
        
        levelist = []
        for level in levels:
            bundle = "Level|" + str(level.level_id) +"|"+ level.name+"|"+level.description+"|"+\
                str(level.category_id)+"|"+str(level.rubric_id)+"|"+\
                level.level_sha +"|"+str(level.points)
            levelist.append(bundle)
            logging.debug(bundle)
                
        return levelist
    
        
    def bundle_score(self, score):
        
        score_bundle = "Score|" + str(score.score_id) + "|" + str(score.project_id) + "|" + \
            str(score.rubric_id) + "|" + str(score.category_id) + "|" + str(score.level_id) + "|" + \
            score.project_sha + "|" + score.rubric_sha + "|" + score.category_sha + "|" +\
            score.level_sha + "|" + str(score.score_count)
        logging.debug(score_bundle)
            
        return score_bundle
