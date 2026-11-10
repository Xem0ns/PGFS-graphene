from data_access import predictions,training_predictions,md_curve,training_loss
"""Portable redrawing of numerical manuscript figures; original supplied PNGs remain in figures/manuscript."""
from pathlib import Path
import argparse,csv,json,os,tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'pgfs_matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from scipy.interpolate import LSQUnivariateSpline
from reproduce_results import ROOT,NAMES,CONV,load_npz

ORDER=['A','FrozenAB','Direct','Inheritance']
COLORS={'A':'#b78222','Direct':'#287bb5','FrozenAB':'#d94466','Inheritance':'#198b75'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'reproduced/figures');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.spines.right':False,'axes.spines.top':False})
    def save(fig,name):
        fig.savefig(a.output/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(a.output/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
    r=load_npz(ROOT/'data/reference_619.npz');pr={k:predictions(k) for k in ORDER};ood=r['role']=='extrapolation';n=r['N'];area=r['area_A2']
    for prop,unit in [('energy','meV/atom'),('force','eV/Å'),('stress','N/m')]:
        fig,axs=plt.subplots(1,4,figsize=(16,3.9),layout='constrained')
        for ax,k in zip(axs,ORDER):
            v=pr[k]
            if prop=='energy':
                x=(r['energy']/n-r['energy'][0]/n[0])*1000;y=(v['energy']/n-v['energy'][0]/n[0])*1000;err=(v['energy']-r['energy'])/n*1000
            elif prop=='force':x=r['forces'];y=v['forces'];err=y-x
            else:x=-r['virial'][:,0,0]/area*CONV;y=-v['virial'][:,0,0]/area*CONV;err=y-x
            xx=x[ood].ravel();yy=y[ood].ravel();rmse=np.sqrt(np.mean(err[ood]**2))
            if prop=='force':ax.hexbin(xx,yy,gridsize=65,mincnt=1,bins='log',cmap='Blues')
            else:ax.scatter(xx,yy,s=10,alpha=.65,color='#3b91ae',edgecolors='none')
            lo=min(xx.min(),yy.min());hi=max(xx.max(),yy.max());pad=.05*(hi-lo);lo-=pad;hi+=pad;ax.plot([lo,hi],[lo,hi],'--',color='#84909a',lw=1);ax.set(xlim=(lo,hi),ylim=(lo,hi),title=NAMES[k],xlabel=f'DFT {prop} ({unit})');ax.text(.04,.92,f'RMSE = {rmse:.4f}',transform=ax.transAxes);ax.set_aspect('equal')
        axs[0].set_ylabel(f'Predicted {prop} ({unit})');save(fig,'extrapolation_'+prop)
    fig,axs=plt.subplots(1,3,figsize=(14,3.8),layout='constrained')
    for ax,k,stage in zip(axs,['FrozenAB','Direct','Inheritance'],['pgfs_residual','jointly_trained','inherited_parameters']):
        z=training_loss(stage)
        series=[('Total',z['total_loss']),('Energy',z['RMSE_E_train_eV_atom']),('Force',z['RMSE_F_train_eV_A']),('0.1 × virial',.1*z['RMSE_virial_train_eV_atom']),('Regularization',z['L1_loss']+z['L2_loss'])]
        for label,y in series:ax.semilogy(z['generation'],y,label=label)
        ax.set(title=NAMES[k],xlabel='Generation')
    axs[0].set_ylabel('Training loss contribution');axs[-1].legend(fontsize=8);save(fig,'training_losses')
    fig,axs=plt.subplots(1,3,figsize=(15,4),layout='constrained');strain=r['strain_percent'];eref=r['energy']/n
    axs[0].plot(strain,(eref-eref[0])*1000,'k',label='DFT');axs[1].plot(strain,-r['virial'][:,0,0]/area*CONV,'k',label='DFT')
    for k in ORDER:
        v=pr[k];e=v['energy']/n;axs[0].plot(strain,(e-e[0])*1000,color=COLORS[k],label=NAMES[k]);axs[1].plot(strain,-v['virial'][:,0,0]/area*CONV,color=COLORS[k]);axs[2].plot(strain,np.sqrt(np.mean((v['forces']-r['forces'])**2,axis=(1,2))),color=COLORS[k])
    for ax in axs:ax.axvline(3,color='.6',ls=':');ax.axvline(12,color='.6',ls=':');ax.axvspan(12,strain.max(),color='#f4e7ca',alpha=.45);ax.set_xlabel('Strain (%)')
    for ax,label in zip(axs,['Relative energy (meV/atom)','Axial stress (N/m)','Per-configuration force RMSE (eV/Å)']):ax.set_ylabel(label)
    axs[0].legend(fontsize=7);save(fig,'profiles_vs_strain')
    with (ROOT/'md/initial_DFT_comparison.csv').open() as f:initial=list(csv.DictReader(f))
    fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
    for ax,field,title in zip(axs,['energy_error_meV_atom','force_component_RMSE_eV_A','stress_xx_error_N_m'],['Energy error (meV/atom)','Force RMSE (eV/Å)','Axial stress error (N/m)']):
        matrix=np.array([[float(next(x[field] for x in initial if x['model']==k and float(x['target_percent'])==target)) for target in [2,8,13]] for k in ORDER]);ax.imshow(abs(matrix),cmap='Blues',aspect='auto');ax.set_xticks(range(3),['2.0075','8.0069','13.0064']);ax.set_yticks(range(4),[NAMES[k] for k in ORDER] if ax==axs[0] else ['']*4);ax.set(xlabel='Initial strain (%)',title=title)
        for i in range(4):
            for j in range(3):ax.text(j,i,f'{matrix[i,j]:.3f}',ha='center',va='center',color='white' if abs(matrix[i,j])>.65*abs(matrix).max() else '#26323a')
    save(fig,'initial_DFT_errors')
    fig,axs=plt.subplots(2,3,figsize=(14,7),layout='constrained')
    for case in json.loads((ROOT/'md/cases.json').read_text()):
        if case['experiment']!='fixed_strain_holds':continue
        path=Path(case['case']);target=int(next(x.removeprefix('strain') for x in path.parts if x.startswith('strain')));j=[2,8,13].index(target);model=path.parts[-2];seed=next(x for x in path.parts if x.startswith('seed'));style={'seed2026110711':':','seed2026110721':'-','seed2026110722':'--'}[seed];z=md_curve(case)
        for row,col in [(0,2),(1,7)]:axs[row,j].plot(z[:,0],z[:,col]*(100 if row==1 else 1),style,color=COLORS[model],lw=1.1)
    for j in range(3):
        axs[0,j].set_title(f'{[2,8,13][j]}% nominal strain');axs[1,j].axhline(99,color='.6',ls=':',lw=1);axs[1,j].set_ylim(85,100.5)
        for row in range(2):axs[row,j].set(xlim=(0,5),xlabel='Hold time (ps)')
    axs[0,0].set_ylabel('Axial stress (N/m)');axs[1,0].set_ylabel('Three-coordinated atoms (%)');fig.legend(handles=[Line2D([0],[0],color=COLORS[k],label=NAMES[k]) for k in ['Direct','FrozenAB','Inheritance']],loc='outside upper center',ncol=3,fontsize=9);save(fig,'common_state_holds')
    fig,axs=plt.subplots(3,1,figsize=(8,9),layout='constrained');dft=np.loadtxt(ROOT/'data/stress_strain_raw.dat');axs[0].plot(dft[:,0],dft[:,1],'k',label='Static DFT reference')
    for k in ['Direct','FrozenAB']:
        z=md_curve('tension_'+k);event=(z[:,5]<.8)|(z[:,6]<.99);end=int(np.flatnonzero(event)[0]) if event.any() else len(z);axs[0].plot(z[:end,1],z[:end,2],color=COLORS[k],label=NAMES[k]);axs[0].plot(z[max(0,end-1):,1],z[max(0,end-1):,2],'--',color=COLORS[k],alpha=.65);axs[1].semilogy(z[:,1],z[:,4],color=COLORS[k]);axs[2].plot(z[:,1],z[:,5],color=COLORS[k])
    for ax,label in zip(axs,['Axial stress (N/m)','Temperature (K)','Minimum pair distance (Å)']):ax.set(xlabel='Strain (%)',ylabel=label,xlim=(0,18.63))
    axs[0].legend();save(fig,'continuous_tension')
    x,y=dft[:,0],dft[:,1];ux,inverse=np.unique(x,return_inverse=True);uy=np.bincount(inverse,weights=y)/np.bincount(inverse);grid=np.linspace(x.min(),x.max(),max(2001,len(ux)));knots=np.arange(3.,x.max(),3.);knots=knots[(knots>grid[0])&(knots<grid[-1])];smooth=LSQUnivariateSpline(grid,np.interp(grid,ux,uy),knots,k=3);low=(x>=0)&(x<=3);slope,intercept=np.polyfit(x[low],y[low],1);baseline=slope*grid+intercept
    fig,ax=plt.subplots(figsize=(8,5),layout='constrained');ax.scatter(x,y,s=3,alpha=.12,color='#29404b');ax.plot(grid,smooth(grid),color='#24343b',label='DFT response');ax.plot(grid,baseline,'--',color='#aa4639',label='Low-strain linear reference');ax.fill_between(grid,smooth(grid),baseline,color='#c7dce6',alpha=.6)
    for target in [5.,10.,15.,18.6]:
        v=float(smooth(target));b=slope*target+intercept;ax.plot([target,target],[v,b],':',color='.5');ax.text(target,(v+b)/2,f'{100*abs(v-b)/abs(b):.1f}%',ha='right')
    ax.set(xlabel='Strain (%)',ylabel='Axial stress (N/m)',xlim=(0,18.63));ax.legend();save(fig,'physical_motivation')
    print('Numerical figures saved to',a.output)

if __name__=='__main__':main()
