import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard.component';

const dashboardRroutes: Routes = [
  {
    path: '',
    component: DashboardComponent,
    children: [
      { path: '', redirectTo: 'sign-in', pathMatch: 'full' },
      // { path: 'sign-in', component: SignInComponent },
      // { path: 'sign-up', component: SignUpComponent },
      // { path: '**', redirectTo: 'sign-in', pathMatch: 'full' },
    ],
  },
];

@NgModule({
  imports: [RouterModule.forChild(dashboardRroutes)],
  exports: [RouterModule]
})
export class DashboardRoutingModule { }
