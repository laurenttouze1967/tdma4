import PhotoSwipeLightbox from 'photoswipe/lightbox';
import 'photoswipe/style.css';

export function initLightbox(selector = '.pswp-gallery') {
  if (!document.querySelector(selector)) return;
  const lightbox = new PhotoSwipeLightbox({
    gallery: selector,
    children: 'a.ph',
    pswpModule: () => import('photoswipe'),
    bgOpacity: 0.94,
    showHideAnimationType: 'zoom',
    imageClickAction: 'next',
    tapAction: 'toggle-controls',
    paddingFn: (vp) => (vp.x < 700 ? { top: 0, bottom: 40, left: 0, right: 0 } : { top: 30, bottom: 60, left: 70, right: 70 }),
    closeTitle: 'Fermer', zoomTitle: 'Zoom', arrowPrevTitle: 'Précédente', arrowNextTitle: 'Suivante',
    errorMsg: "La photo n'a pas pu être chargée.",
  });
  lightbox.on('uiRegister', () => {
    lightbox.pswp?.ui?.registerElement({
      name: 'caption', order: 9, isButton: false, appendTo: 'root',
      onInit: (el, pswp) => {
        el.className = 'pswp__caption';
        pswp.on('change', () => {
          const a = pswp.currSlide?.data.element as HTMLElement | undefined;
          const cap = a?.dataset.cap || '';
          el.textContent = `${cap}${cap ? ' · ' : ''}${pswp.currIndex + 1} / ${pswp.getNumItems()}`;
        });
      },
    });
  });
  lightbox.init();
}
