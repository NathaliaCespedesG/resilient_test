import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { RequestsService } from '../../../../services/requests.service';
import { Role } from '../../../../shared/models/roles';
import { User, Users } from '../../../../shared/models/database-types';
import { NgModel, ValidatorFn } from '@angular/forms';
import { Router } from '@angular/router';
import { ICONS } from '@shared/constants/icons';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ConfirmationService } from 'primeng/api';

@Component({
  selector: 'app-participants',
  templateUrl: './participants.component.html',
  styleUrl: './participants.component.scss'
})
export class ParticipantsComponent implements OnInit {
  currentParticipant: any;
  deviceSummary: any;
  deviceName: string = '';
  deviceDetailsVisible: boolean[] = [];
  editParticipantForm: FormGroup;
  filteredParticipants: User[] = [];
  icons = ICONS;
  isAddParticipantSuccessful: boolean = false;
  isDuplicateUsername: boolean = false;
  participantData: any;
  participantForm: FormGroup;
  participants: User[] = [];
  roles: Role[] = [];
  selectedRole: Role | undefined;
  selectedRows: any[] = [];
  showDialog: boolean = false;
  showEditDialog: boolean = false;
  showParticipantSummaryDialog: boolean = false;
  showDeviceTableDialog: boolean = false;
  showSpinner: boolean = false;
  username: string;
  usernameFilter: string = '';
  withingsAuthURL: string = 'https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc&redirect_uri=https%3A%2F%2Fresilient.ukdri.care%2F&scope=user.activity%2Cuser.metrics%2Cuser.info%2Cuser.sleepevents%2Cuser.rawdata&state=vsGpqaNPVDPOCrik8Fwn1F4369nTHa'

  @ViewChild('usernameInput', { static: false }) usernameInput?: NgModel;

  constructor(
    private _requestsService: RequestsService,
    private _router: Router,
    private _fb: FormBuilder,
    private _confirmationService: ConfirmationService,
    private _elementRef: ElementRef
  ) {

    this.roles = [
      {name: 'study-participant'},
      {name: 'study-partner-participant'},
      {name: 'test'}
    ];

    this.username = '';

    this.participantForm = this._fb.group({
      username: ['', [Validators.required, Validators.minLength(4)]],
      selectedRole: ['', Validators.required]
    });
    this.editParticipantForm = this._fb.group({
      username: ['', [Validators.minLength(4)]],
      selectedRole: ['']
    });
  }

  ngOnInit(): void {
    this.getUsers();
  }

  getUsers(): void{
    this._requestsService.getUsers().subscribe({
      next: (answer: Users) => {
        if (answer) {
          const usersArray: User[] = Object.values(answer.users);
          this.participants = usersArray.filter( user => {
            const role = user['role'].toLowerCase();
            const active = user['active'];
            return role !== 'admin' && role !== 'clinician' && role != 'super_admin' && active;

          });
          this.filteredParticipants = this.participants;
        }
      }
    });
  }

  applyUsernameFilter(): void {
    this.filteredParticipants = this.participants.filter(participant => {
      return participant.username.toLowerCase().includes(this.usernameFilter.toLowerCase());
    });
  }

  onUsernameInputChange(): void {
    this.isDuplicateUsername = false;
    this.isAddParticipantSuccessful = false;
  }

  showAddParticipantModal(): void {
    this.showDialog = true;
    if (this.usernameFilter) {
      this.username = this.usernameFilter
    }
  }

  showEditParticipantModal(): void {
    this.showEditDialog = true;
  }

  addParticipant(): void{

    if (this.participantForm.invalid ){
      this.participantForm.markAllAsTouched();
      return;
    }

    this.showSpinner = true;

    const participantData = {
      username: this.participantForm.value.username,
      role: this.participantForm.value.selectedRole.name,
      password_hash: "NA"
    }
    this._requestsService.addParticipant(participantData).subscribe({
      next: (response) => {
        this.showSpinner = false;
        this.isAddParticipantSuccessful = true;
      },
      error: (error) => {
        this.isDuplicateUsername = error.error.username.status_code = 403 ? true : false;
        this.showSpinner = false;
      }
    }
    );
  }

  editParticipant(): void{
    const formData = this.editParticipantForm.getRawValue();
    formData.selectedRole = formData.selectedRole ? formData.selectedRole.name : '';

    if (!Object.values(formData).some(value => value !== '' || value !== null || value !== undefined)) {
      return;
    }

    if (this.editParticipantForm.invalid ){
      this.editParticipantForm.markAllAsTouched();
      return;
    }

    this.showSpinner = true;
    const participantEditData: Record<string, any> = {};

    if (formData) {
      Object.keys(formData).forEach(key => {
        if (formData[key] !== "" && formData[key] !== null) {
          if (key === "selectedRole") {
            participantEditData['role'] = formData[key];
          } else {
            participantEditData[key] = formData[key];
          }
        }
      });
    }
    participantEditData['userId'] = this.participantData.id;

    this._requestsService.editParticipant(participantEditData).subscribe({
      next: (response) => {
        this.showSpinner = false;
        this.isAddParticipantSuccessful = true;
        this.participantData = {...this.participantData, ...participantEditData};
      },
      error: (error) => {
        this.isDuplicateUsername = error.error.username.status_code = 403 ? true : false;
        this.showSpinner = false;
      }
    }
    );
  }

  deleteConfirmation(event: Event) {
    this._confirmationService.confirm({
        target: event.target as EventTarget,
        message: 'Do you want to delete this participant?',
        header: 'Delete Confirmation',
        icon: 'pi pi-info-circle',
        acceptButtonStyleClass:"p-button-danger p-button-text",
        rejectButtonStyleClass:"p-button-text p-button-text",
        acceptIcon:"none",
        rejectIcon:"none",

        accept: () => {
          const participantData = {
            'userId': this.participantData.id,
            'active': false
          };
          this._requestsService.editParticipant(participantData).subscribe({
            next: (response) => {
              this.isAddParticipantSuccessful = true;
              this.showParticipantSummaryDialog = false;
            },
            error: (error) => {}
          })

        },
        reject: () => {}
    });
  }

  onDialogHide(): void {
    if (this.isAddParticipantSuccessful){
      this.getUsers();
    }
    this.selectedRows = [];
    this.username = '';
    this.showSpinner = false;
    this.isAddParticipantSuccessful = false;
    this.isDuplicateUsername = false;
    if (this.usernameInput) {
      this.usernameInput.control.markAsPristine(); // Reset ngModel state on dialog show
      this.usernameInput.control.markAsUntouched();
    }
    this.participantForm.reset();
    this.editParticipantForm.reset();
  }

  onSelectParticipantLegacy(participant: any) {
    this.showParticipantSummaryDialog = true;
    this.currentParticipant = participant;
    console.log(participant);

    this._router.navigate(
      ['/dashboard/participant-summary'],
      {
        state:{
          username: participant.data.username,
          createdAt: participant.data.created_at
        }
      }
    );
  }

  onSelectParticipant(participant: any) {
    this.showParticipantSummaryDialog = true;
    this.currentParticipant = participant;
    this.participantData = participant.data;
    this.participantData.devicesLoaded = false;

    this._requestsService.getDevicesByUsername(this.participantData.username).subscribe({
      next: (response) => {
        this.participantData.devicesLoaded = true;
        this.participantData.devices = response.devices;
        this.deviceDetailsVisible = new Array(this.participantData.devices.length).fill(false);
      }

    })
  }

  toggleDeviceDetails(index: number): void {
    this.deviceDetailsVisible[index] = !this.deviceDetailsVisible[index];
  }

  showDeviceTable(index: number): void {
    this.showDeviceTableDialog = true;

    const username = this.participantData.username;
    const device_type = this.participantData.devices[index].device_type;
    const device_id = this.icons[device_type].backend_id!;
    this.deviceName = this.icons[device_type].prettyName;

    this._requestsService.getDeviceSummaryByUsername(username, device_id).subscribe({
      next: (response) => {
        console.log(response);
        this.deviceSummary = response[device_id + '_summary'];

      }
    })
  }

}
