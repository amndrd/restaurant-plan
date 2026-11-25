// The panels around the map: the service at a glance (left), the legend and the clock (bottom), the table card
// (right, on a click).
import { ETATS, ALERTE, hhmm } from './service.js';

const NOMS = { tambour: 'Tambour', table: 'Table', 'table haute': 'Table haute' };
const STATUTS = { cuisine: 'En cuisine', pret: 'Prêt', servi: 'Servi' };

export function nomTable(t) {
  return t.nom.replace('Rangée, ', 'Rangée · ').replace('Salle, ', 'Salle · ').replace('Façade, ', 'Façade · ');
}

export class Interface {
  constructor(service) {
    this.s = service;
    this.kpi = document.getElementById('kpi');
    this.fiche = document.getElementById('fiche');
    this.heure = document.getElementById('heure');
    this.choix = null;
  }

  maj() {
    const c = this.s.chiffres();
    this.heure.textContent = hhmm(this.s.t);
    const jauge = Object.entries(ETATS).map(([k, e]) => c.parEtat[k]
      ? `<i style="width:${(100 * c.parEtat[k] / c.total).toFixed(1)}%;background:${e.couleur}"></i>` : '').join('');
    const p = c.prochaine, tp = p && this.s.tables.find(t => t.id === p.table);
    this.kpi.innerHTML = `
      <div class="titre">En salle</div>
      <div class="grand"><b>${c.couverts}</b><span>couverts sur ${c.places} places</span></div>
      <div class="jauge" title="Les tables, par état">${jauge}</div>
      <dl>
        <dt>Tables libres</dt><dd>${c.libres} / ${c.total}</dd>
        <dt>En attente des plats</dt><dd>${c.enAttente}</dd>
        <dt>Attente moyenne</dt><dd>${c.enAttente ? Math.round(c.attente) + ' min' : '—'}</dd>
        <dt>Alertes</dt><dd class="${c.alertes ? 'alerte' : ''}">${c.alertes}</dd>
        <dt>${c.bars > 1 ? 'Aux comptoirs' : 'Au bar'}</dt><dd>${c.bar} / ${c.barPlaces}</dd>
      </dl>
      ${p ? `<div class="resa">Prochaine réservation <b>${hhmm(p.heure)}</b> · ${p.nom}, ${p.couverts} pers. · ${nomTable(tp)}</div>` : ''}`;
    if (this.choix !== null) this.montrer(this.choix);
  }

  montrer(id) {
    this.choix = id;
    if (this.s.bars.some(b => b.id === id)) return this.montrerBar(id);
    const t = this.s.tables.find(x => x.id === id);
    if (!t) return this.cacher();
    const e = ETATS[t.etat], min = Math.round(this.s.attente(t));
    const plats = {};
    for (const p of t.plats) { const k = p.nom + '|' + this.s.statutPlat(p); plats[k] = (plats[k] || 0) + 1; }
    const liste = Object.entries(plats).map(([k, q]) => { const [nom, st] = k.split('|');
      return `<li><span class="q">${q}×</span><span class="p">${nom}</span><span class="s ${st}">${STATUTS[st]}</span></li>`; }).join('');
    const occupe = !['libre', 'reservee', 'debarrasser'].includes(t.etat);
    this.fiche.innerHTML = `
      <div class="tete">
        <div><h2>${nomTable(t)}</h2><p>${t.places} places · ${NOMS[t.type]} · service ${t.serveur}</p></div>
        <button class="fermer" title="Fermer">×</button>
      </div>
      <div class="etat"><i style="background:${t.alerte ? ALERTE : e.couleur}"></i>${e.nom}${t.alerte ? ' · en retard' : ''}</div>
      <div class="chiffres">
        <div><b>${occupe ? t.invites : '—'}</b><span>personnes</span></div>
        <div class="${t.alerte ? 'alerte' : ''}"><b>${t.etat === 'libre' ? '—' : min + '′'}</b><span>${t.etat === 'commandee' ? 'd’attente' : 'dans cet état'}</span></div>
        <div><b>${t.commandeA ? hhmm(t.commandeA) : '—'}</b><span>commande</span></div>
      </div>
      ${liste ? `<h3>Commande</h3><ul>${liste}</ul>` : ''}
      ${t.resa ? `<div class="note">Réservée à <b>${hhmm(t.resa.heure)}</b> au nom de ${t.resa.nom}, ${t.resa.couverts} personnes.</div>` : ''}
      <div class="note">Données provisoires : le service est simulé.</div>`;
    this.fiche.hidden = false;
    this.fiche.querySelector('.fermer').onclick = () => this.cacher();
  }

  // a bar: each group of guests on its stools, with its state and its order
  montrerBar(id) {
    const b = this.s.bars.find(x => x.id === id), enCours = b.groupes.filter(g => g.etat === 'commandee');
    const attente = enCours.length ? Math.round(Math.max(...enCours.map(g => this.s.t - g.depuis))) : null;
    const alerte = b.groupes.some(g => g.alerte);
    const groupes = [...b.groupes].sort((x, y) => x.sieges[0] - y.sieges[0]).map(g => {
      const e = ETATS[g.etat], plats = {};
      for (const p of g.plats) plats[p.nom] = (plats[p.nom] || 0) + 1;
      const sieges = g.sieges.length > 1 ? `${g.sieges[0] + 1}–${g.sieges[g.sieges.length - 1] + 1}` : `${g.sieges[0] + 1}`;
      return `<li class="groupe-bar"><span class="tab">${sieges}</span><span class="p"><b>${g.invites} pers.</b>
        <span class="etat-bar"><i style="background:${g.alerte ? ALERTE : e.couleur}"></i>${e.nom.split(',')[0]} · ${Math.round(this.s.t - g.depuis)}′</span>
        ${Object.keys(plats).length ? `<small>${Object.entries(plats).map(([n, q]) => `${q > 1 ? q + '× ' : ''}${n}`).join(', ')}</small>` : ''}</span></li>`;
    }).join('');
    this.fiche.innerHTML = `
      <div class="tete">
        <div><h2>${b.nom}</h2><p>${b.places} tabourets · service ${b.serveur}</p></div>
        <button class="fermer" title="Fermer">×</button>
      </div>
      <div class="chiffres">
        <div><b>${b.invites}<small> / ${b.places}</small></b><span>au comptoir</span></div>
        <div><b>${enCours.length}</b><span>en attente</span></div>
        <div class="${alerte ? 'alerte' : ''}"><b>${attente === null ? '—' : attente + '′'}</b><span>plus longue attente</span></div>
      </div>
      ${groupes ? `<h3>Au comptoir, par tabouret</h3><ul>${groupes}</ul>` : '<div class="note">Personne au comptoir pour l’instant.</div>'}
      <div class="note">Données provisoires : le service est simulé.</div>`;
    this.fiche.hidden = false;
    this.fiche.querySelector('.fermer').onclick = () => this.cacher();
  }

  cacher() { this.choix = null; this.fiche.hidden = true; this.surFermer?.(); }
}
