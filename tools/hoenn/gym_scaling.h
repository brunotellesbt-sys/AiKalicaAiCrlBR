#ifndef GUARD_JOURNEY_GYM_SCALING_H
#define GUARD_JOURNEY_GYM_SCALING_H
struct Trainer;
u32 JourneyGymBadgeCount(bool32 kanto);
u32 JourneyGymLevel(const struct Trainer *trainer, u32 originalLevel);
#endif
