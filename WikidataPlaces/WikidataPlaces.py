from typing import Optional

from gi.repository import Gtk
from qwikidata.datavalue import GlobeCoordinate

from gramps.gen.const import COLON, GRAMPS_LOCALE as glocale
from gramps.gen.db import DbTxn
from gramps.gen.lib import Place, PlaceName, PlaceType, Url
from gramps.gen.plug import Gramplet
from qwikidata.entity import WikidataItem
from qwikidata.linked_data_interface import get_entity_dict_from_api

_ = glocale.translation.sgettext


def get_place_from_wikidata(entity_id):
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
            wikipedia_url.set_description(f'Wikipedia {link["title"]}:{link["site"]}')
            place.add_url(wikipedia_url)
    # Instance of -> PlaceType
    if 'P31' in claims_groups:
        for claim in claims_groups['P31']:
            if 'Q102496' == claim.mainsnak.datavalue.value['id']:
                place.set_type(PlaceType.PARISH)
            if 'Q1523821' == claim.mainsnak.datavalue.value['id']:
                place.set_type(PlaceType.PARISH)
            if 'Q23442' == claim.mainsnak.datavalue.value['id']:
                place.set_type(PlaceType.UNKNOWN)  # No islands in Gramps
            if 'Q127448' == claim.mainsnak.datavalue.value['id']:
                place.set_type(PlaceType.MUNICIPALITY)  # municipality of Sweden
    if 'P625' in claims_groups:
        for claim in claims_groups['P625']:
            datavalue: GlobeCoordinate = claim.mainsnak.datavalue
            place.set_latitude(str(datavalue.value['latitude']))
            place.set_longitude(str(datavalue.value['longitude']))
    return place


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
            buffer.set_text(f"Adding entity {entity_id} from Wikidata.\n")

            if self.dbstate.db.has_place_gramps_id(entity_id):
                place = self.dbstate.db.get_place_from_gramps_id(entity_id)
                wikidata_place = get_place_from_wikidata(entity_id)
                buffer.insert(buffer.get_end_iter(), f"Updating {place.get_title()} with"
                                                     f" wikidata {wikidata_place.get_title()}\n")
                place.merge(wikidata_place)
            else:
                place = get_place_from_wikidata(entity_id)
                buffer.insert(buffer.get_end_iter(), f"New entry: {place.get_title()}\n")


            with DbTxn(_('Add Wikidata place %s') % entity_id, self.dbstate.db) as trans:
                self.dbstate.db.add_place(place, trans)
                self.dbstate.db.commit_place(place, trans)

        else:
            buffer.set_text(self._instruction_text)
