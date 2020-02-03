from typing import Optional

from gi.repository import Gtk
from qwikidata.datavalue import GlobeCoordinate

from gramps.gen.const import COLON, GRAMPS_LOCALE as glocale
from gramps.gen.db import DbTxn
from gramps.gen.lib import Place, PlaceName, PlaceType, Url, PlaceRef, Date
from gramps.gen.plug import Gramplet
from qwikidata.entity import WikidataItem
from qwikidata.linked_data_interface import get_entity_dict_from_api


PROPERTY_END_TIME = 'P582'
PROPERTY_START_TIME = 'P580'
PROPERTY_LOCATED_IN_PRESENT = 'P3842'
PROPERTY_LOCATED = 'P276'
PROPERTY_LOCATED_IN_ADM = 'P131'
PROPERTY_COORDINATE_LOCATION = 'P625'
PROPERTY_INSTANCE_OF = 'P31'

ITEM_FORMER_COUNTY_OF_SWEDEN = 'Q64624092'
ITEM_URBAN_AREA_IN_SWEDEN = 'Q12813115'
ITEM_BUILDING = 'Q41176'
ITEM_FARM = 'Q131596'
ITEM_HAMLET = 'Q5084'
ITEM_VILLAGE = 'Q532'
ITEM_LARGE_VILLAGE = 'Q26714626'
ITEM_TOWN = 'Q3957'
ITEM_BOROUGH = 'Q5195043'
ITEM_DISTRICT = 'Q149621'
ITEM_NEIGHBORHOOD = 'Q123705'
ITEM_ADM_REGION = 'Q3455524'
ITEM_COUNTY_OF_SWEDEN = 'Q200547'
ITEM_COUNTY = 'Q28575'
ITEM_PROVINCE_OF_SWEDEN = 'Q193556'
ITEM_PROVINCE = 'Q34876'
ITEM_FEDERAL_STATE = 'Q107390'
ITEM_STATE_OF_US = 'Q35657'
ITEM_COUNTRY = 'Q6256'
ITEM_SOVEREIGN_STATE = 'Q3624078'
ITEM_MUNICIPALITY = 'Q15284'
ITEM_MUNICIPALITY_OF_SWEDEN = 'Q127448'
ITEM_PARISH = 'Q102496'
ITEM_SOCKEN = 'Q1523821'
ITEM_ISLAND = 'Q23442'

_ = glocale.translation.sgettext


def get_place_from_wikidata(entity_id):
    parents = set()
    entity = WikidataItem(get_entity_dict_from_api(entity_id))
    claims_groups = entity.get_truthy_claim_groups()
    place = Place()
    place.set_gramps_id(entity_id)

    name = PlaceName()
    name.set_language('sv')
    name.set_value(entity.get_label('sv'))
    place.set_name(name=name)

    place.set_title(entity.get_label('sv'))
    for lang in ['sv', 'en', 'de', 'fi', 'no', 'nn', 'da', 'se']:
        wiki_name = entity.get_label(lang)
        if len(wiki_name):
            place_name = PlaceName()
            place_name.set_language(lang)
            place_name.set_value(wiki_name)
            place.add_alternative_name(name=place_name)
            for alias in entity.get_aliases(lang):
                alt_name = PlaceName()
                alt_name.set_language(lang)
                alt_name.set_value(alias)
                place.add_alternative_name(name=alt_name)

        for link in entity.get_sitelinks(lang).values():
            wikipedia_url = Url()
            wikipedia_url.set_path(link['url'])
            wikipedia_url.set_type('Wikipedia entry')
            wikipedia_url.set_description('Wikipedia %s:%s' % (link["title"], link["site"]))
            place.add_url(wikipedia_url)

    # Instance of -> PlaceType
    if PROPERTY_INSTANCE_OF in claims_groups:
        for claim in claims_groups[PROPERTY_INSTANCE_OF]:
            instance_of = claim.mainsnak.datavalue.value['id']
            if ITEM_PARISH == instance_of:
                place.set_type(PlaceType.PARISH)
            elif ITEM_SOCKEN == instance_of:
                place.set_type(PlaceType.PARISH)
            elif ITEM_ISLAND == instance_of:
                place.set_type(PlaceType.UNKNOWN)  # No islands in Gramps
            elif ITEM_MUNICIPALITY_OF_SWEDEN == instance_of:
                place.set_type(PlaceType.MUNICIPALITY)
            elif ITEM_MUNICIPALITY == instance_of:
                place.set_type(PlaceType.MUNICIPALITY)
            elif ITEM_COUNTRY == instance_of:
                place.set_type(PlaceType.COUNTRY)
            elif ITEM_SOVEREIGN_STATE == instance_of:
                place.set_type(PlaceType.COUNTRY)
            elif ITEM_STATE_OF_US == instance_of:
                place.set_type(PlaceType.STATE)
            elif ITEM_FEDERAL_STATE == instance_of:
                place.set_type(PlaceType.STATE)
            elif ITEM_COUNTY == instance_of:
                place.set_type(PlaceType.COUNTY)
            elif ITEM_COUNTY_OF_SWEDEN == instance_of:
                place.set_type(PlaceType.COUNTY)
            elif ITEM_FORMER_COUNTY_OF_SWEDEN == instance_of:
                place.set_type(PlaceType.COUNTY)
            elif ITEM_PROVINCE_OF_SWEDEN == instance_of:
                place.set_type(PlaceType.PROVINCE)
            elif ITEM_PROVINCE == instance_of:
                place.set_type(PlaceType.PROVINCE)
            elif ITEM_ADM_REGION == instance_of:
                place.set_type(PlaceType.REGION)
            elif ITEM_NEIGHBORHOOD == instance_of:
                place.set_type(PlaceType.NEIGHBORHOOD)
            elif ITEM_DISTRICT == instance_of:
                place.set_type(PlaceType.DISTRICT)
            elif ITEM_BOROUGH == instance_of:
                place.set_type(PlaceType.BOROUGH)
            elif ITEM_TOWN == instance_of:
                place.set_type(PlaceType.TOWN)
            elif ITEM_LARGE_VILLAGE == instance_of:
                place.set_type(PlaceType.VILLAGE)
            elif ITEM_VILLAGE == instance_of:
                place.set_type(PlaceType.VILLAGE)
            elif ITEM_URBAN_AREA_IN_SWEDEN == instance_of:
                place.set_type(PlaceType.VILLAGE)
            elif ITEM_HAMLET == instance_of:
                place.set_type(PlaceType.HAMLET)
            elif ITEM_FARM == instance_of:
                place.set_type(PlaceType.FARM)
            elif ITEM_BUILDING == instance_of:
                place.set_type(PlaceType.BUILDING)

    if PROPERTY_COORDINATE_LOCATION in claims_groups:
        for claim in claims_groups[PROPERTY_COORDINATE_LOCATION]:
            datavalue = claim.mainsnak.datavalue
            place.set_latitude(str(datavalue.value['latitude']))
            place.set_longitude(str(datavalue.value['longitude']))

    extract_located_in(claims_groups, PROPERTY_LOCATED_IN_PRESENT, parents)
    extract_located_in(claims_groups, PROPERTY_LOCATED_IN_ADM, parents)
    extract_located_in(claims_groups, PROPERTY_LOCATED, parents)

    return place, parents


def extract_located_in(claims_groups, located_in, parents):
    if located_in in claims_groups:
        for claim in claims_groups[located_in]:
            if claim.mainsnak.snak_datatype == 'wikibase-item':
                item_id = claim.mainsnak.datavalue.value["id"]
                start = None
                end = None
                for qualifier in claim.qualifiers.values():
                    for qual in qualifier:
                        if qual.snak.property_id == PROPERTY_START_TIME:  # Start time
                            start = qual.snak.datavalue
                        if qual.snak.property_id == PROPERTY_END_TIME:  # End time
                            end = qual.snak.datavalue
                parents.add((item_id, start, end))


class WikidataPlacesGramplet(Gramplet):

    def __init__(self, gui, nav_group=0):
        self._entry = None
        self._text_area = None
        self._instruction_text = _("Enter a entity ID for a place in Wikidata below. "
                                   "Use the 'Look up' button to get data from Wikidata.")
        super().__init__(gui, nav_group)  # This will call init() but declare variables before

    def init(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox = Gtk.Box()

        self._text_area = Gtk.TextView()
        self._text_area.set_wrap_mode(Gtk.WrapMode.WORD)
        self._text_area.set_editable(False)
        buffer = self._text_area.get_buffer()
        buffer.set_text(self._instruction_text)

        label = Gtk.Label()
        label.set_text(_("Entity ID") + COLON)
        self._entry = Gtk.Entry()
        button = Gtk.Button(label=_("Look up"))
        button.connect("clicked", self.run)

        hbox.pack_start(label, False, True, 0)
        hbox.pack_start(self._entry, True, True, 0)
        vbox.pack_start(self._text_area, True, True, 0)
        vbox.pack_start(hbox, False, True, 0)
        vbox.pack_start(button, False, True, 0)

        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add(vbox)
        vbox.show_all()

    def run(self, obj):
        entity_id = self._entry.get_text()
        buffer = self._text_area.get_buffer()
        if len(entity_id):
            buffer.set_text("Adding entity %s from Wikidata.\n" % entity_id)
            todo = set()
            todo.add((entity_id, None, None))
            done = set()
            all_places = set()
            links_to_add = set()

            while len(todo) > 0:
                current_entity, current_start, current_end = todo.pop()
                buffer.insert(buffer.get_end_iter(), "Working on %s:\n" % current_entity)
                done.add(current_entity)
                wikidata_place, parents = get_place_from_wikidata(current_entity)
                for parent, start, end in parents:
                    if parent not in done:
                        todo.add((parent, start, end))
                    if self.dbstate.db.has_place_gramps_id(parent):
                        parent_ref = self.enclosed_by(parent, end, start)
                        wikidata_place.add_placeref(parent_ref)
                    else:
                        links_to_add.add((current_entity, parent, start, end))
                if self.dbstate.db.has_place_gramps_id(current_entity):
                    place = self.dbstate.db.get_place_from_gramps_id(current_entity)
                    buffer.insert(buffer.get_end_iter(),
                                  "Updating %s with wikidata %s\n" % (place.get_title(),
                                                                      wikidata_place.get_title()))
                    place.merge(wikidata_place)
                else:
                    buffer.insert(buffer.get_end_iter(), "New entry: %s\n" % wikidata_place.get_title())
                    place = wikidata_place
                all_places.add(place)

            with DbTxn(_('Add Wikidata places'), self.dbstate.db) as trans:
                for place in all_places:
                    self.dbstate.db.add_place(place, trans)
                    self.dbstate.db.commit_place(place, trans)

            with DbTxn(_('Update parent references (enclosed by)'), self.dbstate.db) as trans:
                for child, parent, start, end in links_to_add:
                    parent_ref = self.enclosed_by(parent, end, start)

                    child_ent = self.dbstate.db.get_place_from_gramps_id(child)
                    child_ent.add_placeref(parent_ref)
                    self.dbstate.db.commit_place(child_ent, trans)

        else:
            buffer.set_text(self._instruction_text)

    def enclosed_by(self, parent, end, start):
        parent_ent = self.dbstate.db.get_place_from_gramps_id(parent)
        parent_ref = PlaceRef()
        parent_ref.set_reference_handle(parent_ent.get_handle())
        if start is not None:
            if end is not None:
                date = Date()

                start_dict = start.get_parsed_datetime_dict()
                end_dict = end.get_parsed_datetime_dict()
                slash2 = False
                date.set(quality=None,
                         modifier=Date.MOD_SPAN,
                         calendar=None,
                         value=((start_dict['day']), (start_dict['month']), (start_dict['year']), False,
                                (end_dict['day']), (end_dict['month']), (end_dict['year']),
                                slash2),
                         text=None)
                parent_ref.set_date_object(date=date)
            else:
                date = Date()
                start_dict = start.get_parsed_datetime_dict()
                date.set(quality=None,
                         modifier=Date.MOD_AFTER,
                         calendar=None,
                         value=((start_dict['day']), (start_dict['month']), (start_dict['year']), False),
                         text=None)
                parent_ref.set_date_object(date=date)
        elif end is not None:
            date = Date()
            end_dict = end.get_parsed_datetime_dict()
            date.set(quality=None,
                     modifier=Date.MOD_BEFORE,
                     calendar=None,
                     value=((end_dict['day']), (end_dict['month']), (end_dict['year']), False),
                     text=None)
            parent_ref.set_date_object(date=date)
        return parent_ref
