import drawsvg as draw
from circuits_new import *
from helpers import rotate_pos_90

def circuit_to_svg(circuit):
  module_drawings: dict[str, draw.Drawing] = {}
  for layer_ref in circuit["layers"].keys():
    for module_ref in circuit["layers"][layer_ref]["modules"].keys():
      module = circuit["layers"][layer_ref]["modules"][module_ref]
      module_drawings[module_ref] = module_to_svg(module, circuit)
  return module_drawings

def module_to_svg(module, circuit):
  module_radius = float(module["radius"])
  components = module["components"]
  connections = module["connections"]
  footprints = circuit["footprints"]
  d = draw.Drawing(500, 500, origin="center")
  outer_radius = module_radius + 15
  d.append(draw.Circle(0, 0, outer_radius, stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Circle(0, 0, outer_radius + 2, stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Arc(0, 0, outer_radius, -35, -15, cw=True, stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Arc(0, 0, outer_radius, 15, 35, cw=True, stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Arc(0, 0, outer_radius, 145, 165, cw=True, stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Arc(0, 0, outer_radius, 195, 215, cw=True, stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Line(outer_radius * math.cos(math.radians(15)), outer_radius * math.sin(math.radians(15)),
                     outer_radius * math.cos(math.radians(15)) + 15, outer_radius * math.sin(math.radians(15)),
                     stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Line(outer_radius * math.cos(math.radians(-15)), outer_radius * math.sin(math.radians(-15)),
                     outer_radius * math.cos(math.radians(-15)) + 15, outer_radius * math.sin(math.radians(-15)),
                     stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Line(outer_radius * math.cos(math.radians(165)), outer_radius * math.sin(math.radians(165)),
                     outer_radius * math.cos(math.radians(165)) - 15, outer_radius * math.sin(math.radians(165)),
                     stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Line(outer_radius * math.cos(math.radians(195)), outer_radius * math.sin(math.radians(195)),
                     outer_radius * math.cos(math.radians(195)) - 15, outer_radius * math.sin(math.radians(195)),
                     stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Arc(outer_radius * math.cos(math.radians(15)) + 15, 0,
                    outer_radius * math.sin(math.radians(15)), 90, 270, 
                    stroke="black", stroke_width=1, fill="none"))
  d.append(draw.Arc(outer_radius * math.cos(math.radians(165)) - 15, 0,
                    outer_radius * math.sin(math.radians(15)), 270, 90, 
                    stroke="black", stroke_width=1, fill="none"))

  for i in range(0, 8):
    start_angle = 35 + i * 30
    end_angle = 25 + (i + 1) * 30
    if i > 3:
      start_angle += 60
      end_angle += 60
    d.append(draw.Line((outer_radius) * math.cos(math.radians(start_angle)),
                       (outer_radius) * math.sin(math.radians(start_angle)),
                       (module_radius) * math.cos(math.radians(start_angle)),
                       (module_radius) * math.sin(math.radians(start_angle)), stroke="black", stroke_width=1, fill="none"))
    d.append(draw.Arc(0, 0, module_radius, start_angle, end_angle, cw=True, stroke="black", stroke_width=1, fill="none"))
    d.append(draw.Line((outer_radius) * math.cos(math.radians(end_angle)),
                       (outer_radius) * math.sin(math.radians(end_angle)),
                       (module_radius) * math.cos(math.radians(end_angle)),
                       (module_radius) * math.sin(math.radians(end_angle)), stroke="black", stroke_width=1, fill="none"))
    if i != 7:
      d.append(draw.Arc(0, 0, outer_radius, end_angle, end_angle + 10, cw=True, stroke="black", stroke_width=1, fill="none"))
  for comp_ref in components.keys():
    component = components[comp_ref]
    comp_pos = Position(float(component["pos"]["x"]), float(component["pos"]["y"]))
    comp_angle = float(component["angle"])
    footprint_ref = comp_ref
    if str(component["is_pad"]) == "True":
      footprint_ref = "pad"
    footprint = footprints[footprint_ref]
    pad_paths = footprint["paths"][2]
    g = draw.Group(stroke="black", stroke_width=1, fill="none", transform=f"rotate({comp_angle},0,0)")
    for (pin_num, shape) in enumerate(pad_paths):
      pad_offset = Position(0, 0)
      for (idx, line) in enumerate(shape["paths"]):
        start_pos = Position(float(line[0]["x"]), float(line[0]["y"])) + pad_offset
        end_pos = Position(float(line[1]["x"]), float(line[1]["y"])) + pad_offset
        g.append(draw.Line(start_pos.x, start_pos.y, end_pos.x, end_pos.y, stroke="black", stroke_width=1, fill="none"))
    d.append(draw.Use(g, comp_pos.x, comp_pos.y))
  for trace_ref in connections.keys():
    trace = connections[trace_ref]
    points = trace["points"]
    trace_width = 3.0
    for (idx, _) in enumerate(points):
      if len(points) == 2 and idx == 1:
        first_point = Position(float(points[idx - 1]["x"]), float(points[idx - 1]["y"]))
        end_point = Position(float(points[idx]["x"]), float(points[idx]["y"]))
        rad = calculate_rad(first_point, mid_point) + math.pi/2
        d.append(draw.Line(first_point.x + trace_width*math.cos(rad), first_point.y - trace_width*math.sin(rad),
                            end_point.x + trace_width*math.cos(rad), end_point.y - trace_width*math.sin(rad), stroke="black", stroke_width=1, fill="none"))
        d.append(draw.Line(first_point.x - trace_width*math.cos(rad), first_point.y + trace_width*math.sin(rad),
                            end_point.x - trace_width*math.cos(rad), end_point.y + trace_width*math.sin(rad), stroke="black", stroke_width=1, fill="none"))
        d.append(draw.Line(end_point.x + trace_width*math.cos(rad), end_point.y - trace_width*math.sin(rad),
                            end_point.x - trace_width*math.cos(rad), end_point.y + trace_width*math.sin(rad), stroke="black", stroke_width=1, fill="none"))
        d.append(draw.Line(first_point.x + trace_width*math.cos(rad), first_point.y - trace_width*math.sin(rad),
                            first_point.x - trace_width*math.cos(rad), first_point.y + trace_width*math.sin(rad), stroke="black", stroke_width=1, fill="none"))
      elif idx > 1:
        first_point = Position(float(points[idx - 2]["x"]), float(points[idx - 2]["y"]))
        mid_point = Position(float(points[idx - 1]["x"]), float(points[idx - 1]["y"]))
        end_point = Position(float(points[idx]["x"]), float(points[idx]["y"]))
        rad1 = calculate_rad(first_point, mid_point) + math.pi/2
        rad2 = calculate_rad(mid_point, end_point) + math.pi/2
        rad_mid = rad1 + (rad2 - rad1)/2
        mid_point_ext1 = Position(mid_point.x + trace_width*math.cos(rad_mid), 
                                  mid_point.y - trace_width*math.sin(rad_mid))
        mid_point_ext2 = Position(mid_point.x - trace_width*math.cos(rad_mid), 
                                  mid_point.y + trace_width*math.sin(rad_mid))
        d.append(draw.Line(mid_point_ext1.x, mid_point_ext1.y,
                            end_point.x + trace_width*math.cos(rad2), end_point.y - trace_width*math.sin(rad2), stroke="black", stroke_width=1, fill="none"))
        d.append(draw.Line(mid_point_ext2.x, mid_point_ext2.y,
                            end_point.x - trace_width*math.cos(rad2), end_point.y + trace_width*math.sin(rad2), stroke="black", stroke_width=1, fill="none"))
        if idx == 2:
          d.append(draw.Line(first_point.x + trace_width*math.cos(rad1), first_point.y - trace_width*math.sin(rad1),
                            mid_point_ext1.x, mid_point_ext1.y, stroke="black", stroke_width=1, fill="none"))
          d.append(draw.Line(first_point.x - trace_width*math.cos(rad1), first_point.y + trace_width*math.sin(rad1),
                            mid_point_ext2.x, mid_point_ext2.y, stroke="black", stroke_width=1, fill="none"))
          d.append(draw.Line(first_point.x + trace_width*math.cos(rad1), first_point.y - trace_width*math.sin(rad1),
                            first_point.x - trace_width*math.cos(rad1), first_point.y + trace_width*math.sin(rad1), stroke="black", stroke_width=1, fill="none"))
        if idx == len(points) - 1:
          d.append(draw.Line(end_point.x + trace_width*math.cos(rad2), end_point.y - trace_width*math.sin(rad2),
                            end_point.x - trace_width*math.cos(rad2), end_point.y + trace_width*math.sin(rad2), stroke="black", stroke_width=1, fill="none"))
  return d
