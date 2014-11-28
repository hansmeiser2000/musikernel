/*
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef MK_THREADS_H
#define	MK_THREADS_H

#ifdef SCHED_DEADLINE

#define RT_SCHED SCHED_DEADLINE

#else

#define RT_SCHED SCHED_FIFO

#endif

#include "edmnext.h"
#include "wavenext.h"

#ifdef	__cplusplus
extern "C" {
#endif

void * v_pydaw_worker_thread(void*);
void v_pydaw_init_worker_threads(int, int);

#ifdef	__cplusplus
}
#endif

void v_pydaw_activate(int a_thread_count,
        int a_set_thread_affinity, char * a_project_path,
        float a_sr, t_midi_device_list * a_midi_devices)
{
    /* Instantiate hosts */
    g_musikernel_get(a_sr);
    g_pydaw_instantiate(a_midi_devices);
    g_wavenext_get();

    v_open_project(pydaw_data, a_project_path, 1);

    v_pydaw_init_worker_threads(a_thread_count, a_set_thread_affinity);
}

void v_pydaw_destructor()
{
    if(pydaw_data)
    {
        musikernel->audio_recording_quit_notifier = 1;
        lo_address_free(musikernel->uiTarget);

        int f_i = 0;

        char tmp_sndfile_name[2048];

        while(f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT)
        {
            if(musikernel->audio_inputs[f_i]->sndfile)
            {
                sf_close(musikernel->audio_inputs[f_i]->sndfile);
                sprintf(tmp_sndfile_name, "%s%i.wav",
                        musikernel->audio_tmp_folder, f_i);
                printf("Deleting %s\n", tmp_sndfile_name);
                remove(tmp_sndfile_name);
            }
            ++f_i;
        }

        f_i = 1;
        while(f_i < musikernel->track_worker_thread_count)
        {
            //pthread_mutex_lock(&pydaw_data->track_block_mutexes[f_i]);
            musikernel->track_thread_quit_notifier[f_i] = 1;
            //pthread_mutex_unlock(&pydaw_data->track_block_mutexes[f_i]);
            ++f_i;
        }

        f_i = 1;
        while(f_i < musikernel->track_worker_thread_count)
        {
            pthread_mutex_lock(&musikernel->track_block_mutexes[f_i]);
            pthread_cond_broadcast(&musikernel->track_cond[f_i]);
            pthread_mutex_unlock(&musikernel->track_block_mutexes[f_i]);
            ++f_i;
        }

        sleep(1);

        f_i = 1;
        while(f_i < musikernel->track_worker_thread_count)
        {
            //abort the application rather than hang indefinitely
            assert(musikernel->track_thread_quit_notifier[f_i] == 2);
            //pthread_mutex_lock(&pydaw_data->track_block_mutexes[f_i]);
            //pthread_mutex_unlock(&pydaw_data->track_block_mutexes[f_i]);
            ++f_i;
        }
    }
}


void * v_pydaw_osc_send_thread(void* a_arg)
{
    t_osc_send_data f_send_data;
    int f_i = 0;

    while(f_i < PYDAW_OSC_SEND_QUEUE_SIZE)
    {
        hpalloc((void**)&f_send_data.osc_queue_vals[f_i],
            sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);
        ++f_i;
    }

    hpalloc((void**)&f_send_data.f_tmp1,
        sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);
    hpalloc((void**)&f_send_data.f_tmp2,
        sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);
    hpalloc((void**)&f_send_data.f_msg,
        sizeof(char) * PYDAW_OSC_MAX_MESSAGE_SIZE);

    f_send_data.f_tmp1[0] = '\0';
    f_send_data.f_tmp2[0] = '\0';
    f_send_data.f_msg[0] = '\0';

    while(!musikernel->audio_recording_quit_notifier)
    {
        if(musikernel->is_ab_ing == 0)
        {
            v_en_osc_send(&f_send_data);
        }
        else if(musikernel->is_ab_ing == 1)
        {
            v_wn_osc_send(&f_send_data);
        }

        usleep(20000);
    }

    printf("osc send thread exiting\n");

    return (void*)1;
}

#if defined(__amd64__) || defined(__i386__)
void cpuID(unsigned int i, unsigned int regs[4])
{
    asm volatile
      ("cpuid" : "=a" (regs[0]), "=b" (regs[1]), "=c" (regs[2]), "=d" (regs[3])
       : "a" (i), "c" (0));
    // ECX is set to zero for CPUID function 4
}

__attribute__((optimize("-O0"))) char * uint_to_char(unsigned int a_input)
{
    char* bytes = (char*)malloc(sizeof(char) * 5);

    bytes[0] = a_input & 0xFF;
    bytes[1] = (a_input >> 8) & 0xFF;
    bytes[2] = (a_input >> 16) & 0xFF;
    bytes[3] = (a_input >> 24) & 0xFF;
    bytes[4] = '\0';

    return bytes;
}

__attribute__((optimize("-O0"))) int i_cpu_has_hyperthreading()
{
    unsigned int regs[4];

    // Get vendor
    cpuID(0, regs);

    char cpuVendor[12];
    sprintf(cpuVendor, "%s%s%s", uint_to_char(regs[1]), uint_to_char(regs[3]),
            uint_to_char(regs[2]));

    // Get CPU features
    cpuID(1, regs);
    unsigned cpuFeatures = regs[3]; // EDX

    // Logical core count per CPU
    cpuID(1, regs);
    unsigned logical = (regs[1] >> 16) & 0xff; // EBX[23:16]
    unsigned cores = logical;

    if(!strcmp(cpuVendor, "GenuineIntel"))
    {
        printf("\nDetected Intel CPU, checking for hyperthreading.\n");
        // Get DCP cache info
        cpuID(4, regs);
        cores = ((regs[0] >> 26) & 0x3f) + 1; // EAX[31:26] + 1
        // Detect hyper-threads
        int hyperThreads = cpuFeatures & (1 << 28) && cores < logical;
        return hyperThreads;

    }
    /*else if(!strcmp(cpuVendor, "AuthenticAMD"))
    {
        return 0;
      // Get NC: Number of CPU cores - 1
      //cpuID(0x80000008, regs);
      //cores = ((unsigned)(regs[2] & 0xff)) + 1; // ECX[7:0] + 1
    }*/
    else
    {
        printf("Detected CPU vendor %s , assuming no hyper-threading.\n",
                cpuVendor);
        return 0;
    }
}
#else
int i_cpu_has_hyperthreading()
{
    return 0;
}
#endif

__attribute__((optimize("-O0"))) void v_self_set_thread_affinity()
{
    pthread_attr_t threadAttr;
    struct sched_param param;
    param.__sched_priority = sched_get_priority_max(RT_SCHED);
    printf(" Attempting to set pthread_self to .__sched_priority = %i\n",
            param.__sched_priority);
    pthread_attr_init(&threadAttr);
    pthread_attr_setschedparam(&threadAttr, &param);
    pthread_attr_setstacksize(&threadAttr, 8388608);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);

    pthread_t f_self = pthread_self();
    pthread_setschedparam(f_self, RT_SCHED, &param);
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    pthread_setaffinity_np(f_self, sizeof(cpu_set_t), &cpuset);

    pthread_attr_destroy(&threadAttr);
}

void * v_pydaw_worker_thread(void* a_arg)
{
    t_pydaw_thread_args * f_args = (t_pydaw_thread_args*)(a_arg);

    int f_thread_num = f_args->thread_num;
    pthread_cond_t * f_track_cond = &musikernel->track_cond[f_thread_num];
    pthread_mutex_t * f_track_block_mutex =
        &musikernel->track_block_mutexes[f_thread_num];
    pthread_spinlock_t * f_lock = &musikernel->thread_locks[f_thread_num];

    while(1)
    {
        pthread_cond_wait(f_track_cond, f_track_block_mutex);
        pthread_spin_lock(f_lock);
        pthread_spin_unlock(f_lock);

        if(musikernel->track_thread_quit_notifier[f_thread_num])
        {
            musikernel->track_thread_quit_notifier[f_thread_num] = 2;
            printf("Worker thread %i exiting...\n", f_thread_num);
            break;
        }

        v_pydaw_process(f_args);
    }

    return (void*)1;
}

void v_pydaw_init_worker_threads(int a_thread_count, int a_set_thread_affinity)
{
    int f_cpu_count = sysconf(_SC_NPROCESSORS_ONLN);
    int f_cpu_core_inc = 1;
    int f_has_ht = i_cpu_has_hyperthreading();

    if(f_has_ht)
    {
        printf("\n\n#####################################################\n");
        printf("Detected Intel hyperthreading, dividing logical"
                " core count by 2.\n");
        printf("You should consider turning off hyperthreading in "
                "your PC's BIOS for best performance.\n");
        printf("#########################################################\n\n");
        f_cpu_count /= 2;
        f_cpu_core_inc = 2;
    }

    if(a_thread_count == 0)
    {
        musikernel->track_worker_thread_count = 1; //f_cpu_count;

        /*if((musikernel->track_worker_thread_count) > 4)
        {
            musikernel->track_worker_thread_count = 4;
        }
        else if((musikernel->track_worker_thread_count) == 4)
        {
            musikernel->track_worker_thread_count = 3;
        }
        else if((musikernel->track_worker_thread_count) <= 0)
        {
            musikernel->track_worker_thread_count = 1;
        }*/
    }
    else
    {
        musikernel->track_worker_thread_count = a_thread_count;
    }

    if(!f_has_ht && ((musikernel->track_worker_thread_count * 2) <= f_cpu_count))
    {
        f_cpu_core_inc = f_cpu_count / musikernel->track_worker_thread_count;

        if(f_cpu_core_inc < 2)
        {
            f_cpu_core_inc = 2;
        }
        else if(f_cpu_core_inc > 4)
        {
            f_cpu_core_inc = 4;
        }
    }

    printf("Spawning %i worker threads\n", musikernel->track_worker_thread_count);

    musikernel->track_block_mutexes =
            (pthread_mutex_t*)malloc(sizeof(pthread_mutex_t) *
                (musikernel->track_worker_thread_count));
    musikernel->track_worker_threads =
            (pthread_t*)malloc(sizeof(pthread_t) *
                (musikernel->track_worker_thread_count));

    lmalloc((void**)&musikernel->track_thread_quit_notifier,
            (sizeof(int) * (musikernel->track_worker_thread_count)));
    lmalloc((void**)&musikernel->track_thread_is_finished,
            (sizeof(int) * (musikernel->track_worker_thread_count)));

    musikernel->track_cond =
            (pthread_cond_t*)malloc(sizeof(pthread_cond_t) *
                (musikernel->track_worker_thread_count));

    musikernel->thread_locks =
        (pthread_spinlock_t*)malloc(sizeof(pthread_spinlock_t) *
            (musikernel->track_worker_thread_count));

    pthread_attr_t threadAttr;
    struct sched_param param;
    param.__sched_priority = sched_get_priority_max(RT_SCHED);
    printf(" Attempting to set .__sched_priority = %i\n",
            param.__sched_priority);
    pthread_attr_init(&threadAttr);
    pthread_attr_setschedparam(&threadAttr, &param);
    pthread_attr_setstacksize(&threadAttr, 8388608);
    pthread_attr_setdetachstate(&threadAttr, PTHREAD_CREATE_DETACHED);
    pthread_attr_setschedpolicy(&threadAttr, RT_SCHED);

    //pthread_t f_self = pthread_self();
    //pthread_setschedparam(f_self, RT_SCHED, &param);

    int f_cpu_core = 0;

    if(a_set_thread_affinity)
    {
        f_cpu_core += f_cpu_core_inc;

        if(f_cpu_core >= f_cpu_count)
        {
            f_cpu_core = 0;
        }
    }



    int f_i = 0;

    while(f_i < (musikernel->track_worker_thread_count))
    {
        musikernel->track_thread_is_finished[f_i] = 0;
        musikernel->track_thread_quit_notifier[f_i] = 0;
        t_pydaw_thread_args * f_args =
                (t_pydaw_thread_args*)malloc(sizeof(t_pydaw_thread_args));
        f_args->thread_num = f_i;

        if(f_i > 0)
        {
            //pthread_mutex_init(&musikernel->track_cond_mutex[f_i], NULL);
            pthread_cond_init(&musikernel->track_cond[f_i], NULL);
            pthread_spin_init(&musikernel->thread_locks[f_i], 0);
            pthread_mutex_init(&musikernel->track_block_mutexes[f_i], NULL);
            pthread_create(&musikernel->track_worker_threads[f_i],
                    &threadAttr, v_pydaw_worker_thread, (void*)f_args);

            if(a_set_thread_affinity)
            {
                cpu_set_t cpuset;
                CPU_ZERO(&cpuset);
                CPU_SET(f_cpu_core, &cpuset);
                pthread_setaffinity_np(musikernel->track_worker_threads[f_i],
                        sizeof(cpu_set_t), &cpuset);
                //sched_setaffinity(0, sizeof(cpu_set_t), &cpuset);
                f_cpu_core += f_cpu_core_inc;
            }

            struct sched_param param2;
            int f_applied_policy = 0;
            pthread_getschedparam(musikernel->track_worker_threads[f_i],
                &f_applied_policy, &param2);

            if(f_applied_policy == RT_SCHED)
            {
                printf("Scheduling successfully applied with priority %i\n ",
                        param2.__sched_priority);
            }
            else
            {
                printf("Scheduling was not successfully applied\n");
            }
        }
        else
        {
            musikernel->main_thread_args = (void*)f_args;
        }
        ++f_i;
    }

    pthread_attr_destroy(&threadAttr);
    musikernel->audio_recording_quit_notifier = 0;


    pthread_attr_t auxThreadAttr;
    pthread_attr_init(&auxThreadAttr);
    pthread_attr_setdetachstate(&auxThreadAttr, PTHREAD_CREATE_DETACHED);

    /*The worker thread for flushing recorded audio from memory to disk*/
    /*No longer recording audio in PyDAW, but keeping the code here for
     * when I bring it back...*/
    /*pthread_create(&musikernel->audio_recording_thread, &threadAttr,
        v_pydaw_audio_recording_thread, NULL);*/

    pthread_create(&musikernel->osc_queue_thread, &auxThreadAttr,
            v_pydaw_osc_send_thread, (void*)musikernel);
    pthread_attr_destroy(&auxThreadAttr);
}




#endif	/* MK_THREADS_H */
