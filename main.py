import bpy
import sys
import os
import json

CATEGORY_PAWN = "Pawn"
CATEGORY_SCENE = "Scene"
CATEGORY_PLACE = "Place"
CATEGORY_PART = "Part"
CATEGORY_WHOLE = "Whole"

pawn_data_format = ["TOKEN_ID", "ID", "Hat", "Head", "Jacket", "Trousers", "Shoes", "Type"]
composite_data_format = ["Target", "Pawns"]
base_dir = os.path.dirname(os.path.abspath(__file__))

def check_pawn_param(pawn_param):
    for k in pawn_data_format:
        if k not in pawn_param:
            print("pawn input format error : " + k + " not found")
            return False
    return True

def check_composite_param(composite_param):
    for k in composite_data_format:
        if k not in composite_param:
            print("composite input format error : " + k + " not found")
            return False
    return True

def make_pawn(global_config, composition_data, resource_data, pawn_param, apply_pose):
    pawn_id = pawn_param["ID"]

    composition_data_founded = None
    for c in composition_data:
        c_id = round(c["ID"])
        if((c_id == pawn_id) and (c["Type"] == CATEGORY_PAWN)):
            composition_data_founded = c
            break
    
    if composition_data_founded == None:
        print("composition data not found ! please check composition.xls or run generate_config script! ID : " + str(pawn_id))
        return False

    # components

    component_objects = []
    components = pawn_data_format[2:]
    for comp_name in components:

        comp_id = pawn_param[comp_name]

        if comp_id == -1:
            continue

        res_founded = None
        for r in resource_data:
            r_id = round(r["ID"])
            if((r_id == comp_id) and (r["Category"] == comp_name)):
                res_founded = r
                break

        if res_founded == None:
            print("resource data not found ! please check resource.xls or run generate_config script! ID : " + str(comp_id))
            return False

        comp_filepath = os.path.abspath(os.path.join(base_dir, "input", res_founded["FilePath"]))
        bpy.ops.import_scene.fbx( filepath = comp_filepath, automatic_bone_orientation = True, force_connect_children = True )

        component_objects.append(bpy.context.selected_objects[:])
    
    # pose 

    pose_id = global_config["DefaultPoseID"]
    if apply_pose == True:
        pose_id = round(composition_data_founded["Pawn_PoseID"])

        res_founded = None
        for r in resource_data:
            r_id = round(r["ID"])
            if((r_id == pose_id) and (r["Category"] == "Pose")):
                res_founded = r
                break

        if res_founded == None:
            print("resource data not found ! please check resource.xls or run generate_config script! ID : " + str(pose_id))
            return False

        pose_filepath = os.path.abspath(os.path.join(base_dir, "input", res_founded["FilePath"]))
        bpy.ops.import_scene.fbx( filepath = pose_filepath, automatic_bone_orientation = True, force_connect_children = True )

        pose_objects = bpy.context.selected_objects[:]
        bpy.ops.object.select_all(action='DESELECT')

        for comp_obj in component_objects:
            if(comp_obj[0].animation_data == None):
                comp_obj[0].animation_data_create()
            comp_obj[0].animation_data.action = bpy.data.actions[0]

        bpy.ops.object.select_all(action='DESELECT')

        for pose in pose_objects:
            pose.select_set(True)

        bpy.ops.object.delete()

    # item
    
    if apply_pose == True:
        item_lefthand = -1
        item_righthand = -1
        if(composition_data_founded["Pawn_LeftHandID"] != ""):
            item_lefthand = round(composition_data_founded["Pawn_LeftHandID"])
        if(composition_data_founded["Pawn_RightHandID"] != ""):
            item_righthand = round(composition_data_founded["Pawn_RightHandID"])

        if item_lefthand != -1:
            res_founded = None
            for r in resource_data:
                r_id = round(r["ID"])
                if((r_id == item_lefthand) and (r["Category"] == "Item")):
                    res_founded = r
                    break

            if res_founded == None:
                print("resource data not found ! please check resource.xls or run generate_config script! ID : " + str(item_lefthand))
                return False

            item_filepath = os.path.abspath(os.path.join(base_dir, "input", res_founded["FilePath"]))
            bpy.ops.import_scene.fbx( filepath = item_filepath )


        if item_righthand != -1:
            res_founded = None
            for r in resource_data:
                r_id = round(r["ID"])
                if((r_id == item_righthand) and (r["Category"] == "Item")):
                    res_founded = r
                    break

            if res_founded == None:
                print("resource data not found ! please check resource.xls or run generate_config script! ID : " + str(item_righthand))
                return False

            item_filepath = os.path.abspath(os.path.join(base_dir, "input", res_founded["FilePath"]))
            bpy.ops.import_scene.fbx( filepath = item_filepath )
    
    return True


def make_composite(global_config, composition_data, resource_data, composite_param):
    target_id = composite_param["Target"]
    
    composite_tree = {}
    composite_tree["ID"] = target_id
    composite_tree["IsRoot"] = 1

    def construct(node, root_position):
        node_id = node["ID"]
        node_composition_data_founded = None
        for c in composition_data:
            c_id = round(c["ID"])
            if(c_id == node_id):
                node_composition_data_founded = c
                break

        if node_composition_data_founded == None:
            print("composition data not found ! please check composition.xls or run generate_config script! ID : " + str(node_id))
            return

        node["Type"] = node_composition_data_founded["Type"]
        node_world_pos = eval(node_composition_data_founded["Position"])

        if "IsRoot" in node:
            root_position = node_world_pos
            node["Position"] = [0, 0, 0]
        else:
            node["Position"] = [node_world_pos[0] - root_position[0], node_world_pos[1] - root_position[1], node_world_pos[2] - root_position[2]]

        if node["Type"] == CATEGORY_SCENE:
            # load scene file
            scene_res_id = node_composition_data_founded["Scene_ResID"]
            res_founded = None
            for r in resource_data:
                r_id = round(r["ID"])
                if((r_id == scene_res_id) and (r["Category"] == CATEGORY_SCENE)):
                    res_founded = r
                    break

            if res_founded == None:
                print("resource data not found ! please check resource.xls or run generate_config script! ID : " + str(scene_res_id))
                return

            scene_res_filepath = os.path.abspath(os.path.join(base_dir, "input", res_founded["FilePath"]))
            bpy.ops.import_scene.fbx( filepath = scene_res_filepath, automatic_bone_orientation = True, force_connect_children = True )
            scene_objects = bpy.context.selected_objects[:]
            for scene_object in scene_objects:
                scene_object.location = (node["Position"][0], node["Position"][1], node["Position"][2])

        if node["Type"] == CATEGORY_PAWN:
            # load pawn file
            pawn_id = node["ID"]
            pawn_token_id = None
            for pawn_data in composite_param["Pawns"]:
                if pawn_id == pawn_data["ID"] :
                    pawn_token_id = pawn_data["TOKEN_ID"]
                    break
            
            pawn_filepath = os.path.abspath(os.path.join(base_dir, "output", CATEGORY_PAWN ,str(pawn_id), CATEGORY_PAWN + "_" + str(pawn_token_id) + ".glb"))
            if os.path.isfile(pawn_filepath) == False:
                print("pawn file not found ! please generate this pawn before composite  ID : " + str(pawn_id) + " TOKEN_ID : " + str(pawn_token_id) + " Path :" + str(pawn_filepath))
                return
            
            bpy.ops.import_scene.gltf( filepath = pawn_filepath, bone_heuristic = 'BLENDER')
            pawn_objects = bpy.context.selected_objects[:]
            for pawn_object in pawn_objects:
                pawn_object.location = (node["Position"][0], node["Position"][1], node["Position"][2])
            
            return

        node["Children"] = []
        for c in composition_data:
            c_id = round(c["ID"])
            c_parent_id = round(c["ParentID"])
            if c_parent_id == node_id:
                child_node = {}
                child_node["ID"] = c_id
                node["Children"].append(child_node)

        for child_node in node["Children"]:
            construct(child_node, root_position)

    construct(composite_tree, [0, 0, 0])

    return



def export_picture(export_filepath, resolution_2d):
    bpy.context.scene.render.image_settings.file_format='PNG'
    bpy.context.scene.render.filepath = export_filepath
    bpy.context.scene.render.resolution_x = resolution_2d["x"]
    bpy.context.scene.render.resolution_y = resolution_2d["y"]
    bpy.ops.render.render(write_still=True)

def export_model(export_filepath):
    bpy.ops.export_scene.gltf(filepath = export_filepath)


def main(argv):
    output_path = os.path.join(base_dir, "output")
    output_mode = int(argv[0])
    input_param = json.loads(argv[1])

    composition_json_filepath = os.path.join(base_dir, "composition.json")
    composition_json_file = open(composition_json_filepath)
    composition_data = json.load(composition_json_file)

    resource_json_filepath = os.path.join(base_dir, "resource.json")
    resource_json_file = open(resource_json_filepath)
    resource_data = json.load(resource_json_file)

    config_json_filepath = os.path.join(base_dir, "config.json")
    config_json_file = open(config_json_filepath)
    global_config = json.load(config_json_file)

    # delete the default cube
    objs = bpy.data.objects
    objs.remove(objs["Cube"], do_unlink=True)

    # make and export
    if (output_mode == 0) or (output_mode == 1):
        pawn_param = input_param
        if check_pawn_param(pawn_param) == False :
            return

        make_successed = make_pawn(global_config, composition_data, resource_data, pawn_param, output_mode == 1)
        if make_successed == True:
            #picture
            pawn_picture_filename = CATEGORY_PAWN + "_" + str(pawn_param["TOKEN_ID"]) + ".png"
            pawn_picture_filepath = os.path.join(output_path, "pawn", str(pawn_param["ID"]), pawn_picture_filename)
            resolution_2d = global_config["Resolution"][CATEGORY_PAWN]
            export_picture(pawn_picture_filepath, resolution_2d)

            #model
            pawn_model_filename = CATEGORY_PAWN + "_" + str(pawn_param["TOKEN_ID"]) + ".glb"
            pawn_model_filepath = os.path.join(output_path, "pawn", str(pawn_param["ID"]), pawn_model_filename)
            export_model(pawn_model_filepath)

    
    if (output_mode == 2):
        composite_param = input_param
        if check_composite_param(composite_param) == False :
            return

        make_composite(global_config, composition_data, resource_data, composite_param)

        target_id = composite_param["Target"]
        composition_data_founded = None
        for c in composition_data:
            c_id = round(c["ID"])
            if(c_id == target_id):
                composition_data_founded = c
                break
        if composition_data_founded == None:
            print("composition data not found ! please check composition.xls or run generate_config script! ID : " + str(target_id))
            return

        target_type = composition_data_founded["Type"]

        #picture
        composite_picture_filename = target_type + "_" + str(composite_param["TOKEN_ID"]) + ".png"
        composite_picture_filepath = os.path.join(output_path, target_type.lower(), composite_picture_filename)
        resolution_2d = global_config["Resolution"][target_type]
        export_picture(composite_picture_filepath, resolution_2d)

        #model
        #composite_model_filename = target_type + "_" + composite_param["TOKEN_ID"] + ".glb"
        #composite_model_filepath = os.path.join(output_path, target_type.lower(), composite_model_filename)
        #export_model(composite_model_filepath)


    # do some cleaning
    composition_json_file.close()
    resource_json_file.close()
    config_json_file.close()

if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]  # get all args after "--"
    try:
        main(argv)
    except Exception as e:
        print(e)


